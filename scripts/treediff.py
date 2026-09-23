#!/usr/bin/env python3
"""TUI porovnání dvou adresářů — treediff.

Projde rekurzivně adresáře A a B, vypíše seznam všech souborů (sjednocení
obou stromů) a u každého ukáže stav:

    only A     soubor je jen v prvním adresáři
    only B     soubor je jen v druhém adresáři
    same       soubor je v obou a je bajtově shodný
    +N -M      soubor se liší o N přidaných a M ubraných řádků
    bin diff   soubor je v obou, je binární a liší se

Ovládání:
    šipky / j k / PgUp PgDn / Home End   pohyb v seznamu
    Enter nebo kliknutí myší             otevře vimdiff mezi A/soubor a B/soubor
                                         (pokud je jen v jednom, otevře vim)
    /                                    filtr podle jména
    q                                    konec

Použití:
    ./treediff.py a/ b/
"""

import argparse
import curses
import difflib
import os
import subprocess
import sys
from pathlib import Path


def walk_files(root: Path):
    """Vrátí množinu relativních cest ke všem souborům pod `root`."""
    files = set()
    if not root.is_dir():
        return files
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            full = Path(dirpath) / name
            try:
                rel = full.relative_to(root)
            except ValueError:
                continue
            files.add(rel)
    return files


def is_binary(path: Path):
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
    except OSError:
        return True
    return b"\x00" in chunk


def read_text_lines(path: Path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def linecount(path: Path):
    """Počet řádků textového souboru (binární => 0)."""
    if is_binary(path):
        return 0
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def compare(a: Path, b: Path):
    """Porovná dva existující soubory. Vrátí (status, plus, minus).

    status: 'same' | 'diff' | 'bindiff'
    """
    try:
        sa = a.stat().st_size
        sb = b.stat().st_size
    except OSError:
        return ("bindiff", 0, 0)

    # Rychlá cesta: shodná velikost a shodné bajty => stejné.
    if sa == sb and files_equal(a, b):
        return ("same", 0, 0)

    if is_binary(a) or is_binary(b):
        return ("bindiff", 0, 0)

    try:
        la = read_text_lines(a)
        lb = read_text_lines(b)
    except OSError:
        return ("bindiff", 0, 0)

    plus = minus = 0
    for line in difflib.unified_diff(la, lb, n=0):
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            plus += 1
        elif line.startswith("-"):
            minus += 1
    if plus == 0 and minus == 0:
        return ("same", 0, 0)
    return ("diff", plus, minus)


def files_equal(a: Path, b: Path):
    try:
        with open(a, "rb") as fa, open(b, "rb") as fb:
            while True:
                ba = fa.read(65536)
                bb = fb.read(65536)
                if ba != bb:
                    return False
                if not ba:
                    return True
    except OSError:
        return False


class Entry:
    __slots__ = ("rel", "status", "plus", "minus")

    def __init__(self, rel, status, plus=0, minus=0):
        self.rel = rel            # relativní cesta (str)
        self.status = status      # 'onlyA' 'onlyB' 'same' 'diff' 'bindiff'
        self.plus = plus
        self.minus = minus

    def status_text(self):
        if self.status == "onlyA":
            return "only A"
        if self.status == "onlyB":
            return "only B"
        if self.status == "same":
            return "same"
        if self.status == "bindiff":
            return "bin diff"
        return f"+{self.plus} -{self.minus}"


def build_entries(dir_a: Path, dir_b: Path, progress=None):
    fa = walk_files(dir_a)
    fb = walk_files(dir_b)
    allrel = sorted(fa | fb, key=lambda p: str(p))
    entries = []
    total = len(allrel)
    for i, rel in enumerate(allrel):
        in_a = rel in fa
        in_b = rel in fb
        if in_a and not in_b:
            # jen v A => při přechodu A->B všechny řádky ubrané (minus)
            entries.append(Entry(str(rel), "onlyA", 0, linecount(dir_a / rel)))
        elif in_b and not in_a:
            # jen v B => všechny řádky přidané (plus)
            entries.append(Entry(str(rel), "onlyB", linecount(dir_b / rel), 0))
        else:
            status, plus, minus = compare(dir_a / rel, dir_b / rel)
            entries.append(Entry(str(rel), status, plus, minus))
        if progress and (i % 20 == 0 or i == total - 1):
            progress(i + 1, total)
    return entries


class Node:
    """Uzel stromu — buď adresář (is_dir), nebo soubor."""
    __slots__ = ("name", "rel", "is_dir", "children", "_childmap",
                 "status", "plus", "minus", "expanded")

    def __init__(self, name, rel, is_dir):
        self.name = name          # jméno v rámci rodiče
        self.rel = rel            # relativní cesta od kořene
        self.is_dir = is_dir
        self.children = []        # seřazený seznam potomků (adresáře, pak soubory)
        self._childmap = {}       # pomocná mapa jméno->Node při stavbě
        self.status = "same"
        self.plus = 0
        self.minus = 0
        self.expanded = False     # adresáře jsou defaultně sbalené

    def status_text(self):
        if self.status == "onlyA":
            return "only A"
        if self.status == "onlyB":
            return "only B"
        if self.status == "same":
            return "same"
        if self.status == "bindiff":
            return "bin diff"
        if self.plus == 0 and self.minus == 0:
            return "diff"     # liší se, ale beze změny řádků (binární obsah)
        return f"+{self.plus} -{self.minus}"


def build_tree(entries):
    """Postaví strom z ploché sady souborů a agreguje verdikty adresářů."""
    root = Node("", "", True)
    root.expanded = True
    for e in entries:
        parts = e.rel.split("/")
        node = root
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            if part not in node._childmap:
                relpath = "/".join(parts[:i + 1])
                child = Node(part, relpath, not is_last)
                node._childmap[part] = child
            node = node._childmap[part]
            if is_last:
                node.status = e.status
                node.plus = e.plus
                node.minus = e.minus
    _finalize(root)
    return root


def _finalize(node):
    """Post-order: seřadí potomky a agreguje status/plus/minus adresářů."""
    if not node.is_dir:
        return
    # adresáře první, pak soubory, vše abecedně
    node.children = sorted(
        node._childmap.values(), key=lambda n: (not n.is_dir, n.name.lower()))
    node._childmap = {}
    for k in node.children:
        _finalize(k)
    node.plus = sum(k.plus for k in node.children)
    node.minus = sum(k.minus for k in node.children)
    statuses = {k.status for k in node.children}
    if statuses == {"onlyA"}:
        node.status = "onlyA"
    elif statuses == {"onlyB"}:
        node.status = "onlyB"
    elif statuses == {"same"}:
        node.status = "same"
    else:
        node.status = "diff"


def flatten(root):
    """Viditelné uzly v pořadí zobrazení jako (node, depth)."""
    out = []

    def rec(node, depth):
        for k in node.children:
            out.append((k, depth))
            if k.is_dir and k.expanded:
                rec(k, depth + 1)

    rec(root, 0)
    return out


def collect_files(root):
    """Všechny listové (souborové) uzly — pro režim filtru."""
    out = []

    def rec(node):
        for k in node.children:
            if k.is_dir:
                rec(k)
            else:
                out.append(k)

    rec(root)
    return out


# přemapuje `q` na "quit all" (:qa) — u vimdiffu zavře obě okna najednou
QUIT_ALL = ["-c", "nnoremap q :qa<CR>"]


def open_diff(dir_a: Path, dir_b: Path, entry):
    """Spustí vimdiff obou stran.

    I když soubor existuje jen v jednom adresáři, spustí se vimdiff proti
    chybějící (prázdné) druhé straně, aby byl rozdíl vidět.
    """
    pa = dir_a / entry.rel
    pb = dir_b / entry.rel
    _run(["vimdiff", *QUIT_ALL, str(pa), str(pb)])


def open_side(dir_a: Path, dir_b: Path, entry, side):
    """Otevře jen jednu stranu vybrané položky ve vimu ('left'=A, 'right'=B)."""
    path = (dir_a if side == "left" else dir_b) / entry.rel
    _run(["vim", *QUIT_ALL, str(path)])


def _run(cmd):
    """Dočasně opustí curses a spustí příkaz."""
    curses.endwin()
    try:
        subprocess.call(cmd)
    except FileNotFoundError as e:
        print(f"Nelze spustit {cmd[0]}: {e}", file=sys.stderr)
        input("Stiskni Enter pro návrat...")


def safe_addnstr(win, y, x, s, n, attr=0):
    """addnstr, který nespadne na zápisu do pravého dolního rohu."""
    if n <= 0:
        return
    try:
        win.addnstr(y, x, s, n, attr)
    except curses.error:
        pass


STATUS_ATTR = {
    "onlyA": lambda: curses.color_pair(1),
    "onlyB": lambda: curses.color_pair(2),
    "same": lambda: curses.color_pair(3),
    "diff": lambda: curses.color_pair(4),
    "bindiff": lambda: curses.color_pair(4),
}


def set_expanded_all(node, value):
    for k in node.children:
        if k.is_dir:
            k.expanded = value
            set_expanded_all(k, value)


def run_tui(stdscr, dir_a: Path, dir_b: Path, root):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_YELLOW, -1)   # only A
    curses.init_pair(2, curses.COLOR_CYAN, -1)     # only B
    curses.init_pair(3, curses.COLOR_GREEN, -1)    # same
    curses.init_pair(4, curses.COLOR_RED, -1)      # diff
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)  # selection
    curses.init_pair(6, curses.COLOR_BLUE, -1)     # adresáře
    try:
        curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED)
    except curses.error:
        pass

    sel = 0
    top = 0
    filt = ""
    hide_same = False
    hide_only = False
    all_files = collect_files(root)

    def collect_expanded(node, acc):
        for k in node.children:
            if k.is_dir:
                if k.expanded:
                    acc.add(k.rel)
                collect_expanded(k, acc)

    def apply_expanded(node, expanded_rels):
        for k in node.children:
            if k.is_dir:
                k.expanded = k.rel in expanded_rels
                apply_expanded(k, expanded_rels)

    def reload():
        """Znovu načte a porovná oba stromy; zachová rozbalené adresáře."""
        nonlocal root, all_files
        h, w = stdscr.getmaxyx()
        safe_addnstr(stdscr, h - 1, 0, " Načítám...".ljust(w), w - 1,
                     curses.A_REVERSE)
        stdscr.refresh()
        expanded_rels = set()
        collect_expanded(root, expanded_rels)
        entries = build_entries(dir_a, dir_b)
        root = build_tree(entries)
        apply_expanded(root, expanded_rels)
        all_files = collect_files(root)

    def file_hidden(node):
        if hide_same and node.status == "same":
            return True
        if hide_only and node.status in ("onlyA", "onlyB"):
            return True
        return False

    def node_visible(node):
        # adresář je vidět, jen když má aspoň jednoho viditelného potomka
        if node.is_dir:
            return any(node_visible(c) for c in node.children)
        return not file_hidden(node)

    def build_view():
        """Vrátí seznam (node, depth) k zobrazení."""
        if filt:
            f = filt.lower()
            return [(n, 0) for n in all_files
                    if f in n.rel.lower() and not file_hidden(n)]
        out = []

        def rec(node, depth):
            for k in node.children:
                if not node_visible(k):
                    continue
                out.append((k, depth))
                if k.is_dir and k.expanded:
                    rec(k, depth + 1)

        rec(root, 0)
        return out

    def activate(node):
        """Enter/klik: adresář rozbalí/sbalí, soubor otevře ve vimdiffu."""
        if node.is_dir:
            node.expanded = not node.expanded
        else:
            open_diff(dir_a, dir_b, node)
            stdscr.clear()

    while True:
        view = build_view()
        if sel >= len(view):
            sel = max(0, len(view) - 1)
        h, w = stdscr.getmaxyx()
        body_h = h - 2  # header + footer
        if sel < top:
            top = sel
        elif sel >= top + body_h:
            top = sel - body_h + 1

        stdscr.erase()

        # Hlavička
        flags = []
        if hide_same:
            flags.append("skryté same")
        if hide_only:
            flags.append("skryté only")
        flag_txt = ("  [" + ", ".join(flags) + "]") if flags else ""
        header = f" A: {dir_a}   B: {dir_b}   ({len(view)}){flag_txt}"
        safe_addnstr(stdscr, 0, 0, header.ljust(w), w - 1, curses.A_REVERSE)

        status_w = 12
        for i in range(body_h):
            idx = top + i
            if idx >= len(view):
                break
            node, depth = view[idx]
            y = i + 1
            st = node.status_text()
            if node.is_dir:
                marker = "▾ " if node.expanded else "▸ "
                label = node.name + "/"
            else:
                marker = "  "
                label = node.name if not filt else node.rel
            indent = "  " * depth
            text = f"  {st.ljust(status_w)} {indent}{marker}{label}"
            if idx == sel:
                safe_addnstr(stdscr, y, 0, text.ljust(w), w - 1, curses.color_pair(5))
            else:
                attr = STATUS_ATTR.get(node.status, lambda: 0)()
                safe_addnstr(stdscr, y, 2, st.ljust(status_w), status_w, attr)
                name_x = 2 + status_w + 1
                name_attr = curses.color_pair(6) | curses.A_BOLD if node.is_dir else 0
                safe_addnstr(stdscr, y, name_x, f"{indent}{marker}{label}",
                             max(0, w - name_x - 1), name_attr)

        if filt:
            footer = f" filtr: {filt}   (Enter potvrdí, Esc zruší)"
        else:
            footer = (" ↑↓/jk  →←/Enter/klik rozbal·vimdiff  "
                      "s skrýt same  o skrýt only  a rozbalit vše  "
                      "h/l vim A/B  r reload  / filtr  q konec")
        safe_addnstr(stdscr, h - 1, 0, footer.ljust(w), w - 1, curses.A_REVERSE)
        stdscr.refresh()

        ch = stdscr.getch()

        if ch == ord("q") and not filt:
            return
        elif ch in (curses.KEY_DOWN, ord("j")):
            sel = min(len(view) - 1, sel + 1)
        elif ch in (curses.KEY_UP, ord("k")):
            sel = max(0, sel - 1)
        elif ch == curses.KEY_NPAGE:
            sel = min(len(view) - 1, sel + body_h)
        elif ch == curses.KEY_PPAGE:
            sel = max(0, sel - body_h)
        elif ch == curses.KEY_HOME:
            sel = 0
        elif ch == curses.KEY_END:
            sel = len(view) - 1
        elif ch == curses.KEY_RIGHT:
            if view and view[sel][0].is_dir:
                view[sel][0].expanded = True
        elif ch == curses.KEY_LEFT:
            if view and view[sel][0].is_dir and view[sel][0].expanded:
                view[sel][0].expanded = False
        elif ch in (ord("h"), ord("H")):
            if view and not view[sel][0].is_dir:
                open_side(dir_a, dir_b, view[sel][0], "left")
                stdscr.clear()
        elif ch in (ord("l"), ord("L")):
            if view and not view[sel][0].is_dir:
                open_side(dir_a, dir_b, view[sel][0], "right")
                stdscr.clear()
        elif ch in (curses.KEY_ENTER, 10, 13):
            if view:
                activate(view[sel][0])
        elif ch == ord("s"):
            hide_same = not hide_same
            sel = 0
            top = 0
        elif ch == ord("o"):
            hide_only = not hide_only
            sel = 0
            top = 0
        elif ch == ord("a"):
            # přepne rozbalení celého stromu podle prvního adresáře
            want = not any(k.expanded for k in root.children if k.is_dir)
            set_expanded_all(root, want)
        elif ch == ord("r"):
            reload()
            sel = min(sel, max(0, len(build_view()) - 1))
        elif ch == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
            except curses.error:
                continue
            row = my - 1
            if 0 <= row < body_h and top + row < len(view):
                sel = top + row
                if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED):
                    activate(view[sel][0])
        elif ch == ord("/"):
            filt = _prompt_filter(stdscr, filt)
            sel = 0
            top = 0


def _prompt_filter(stdscr, current):
    """Jednoduchý editovací režim pro filtr; vrátí nový řetězec."""
    filt = current
    h, w = stdscr.getmaxyx()
    while True:
        prompt = f" filtr: {filt}"
        safe_addnstr(stdscr, h - 1, 0, prompt.ljust(w), w - 1, curses.A_REVERSE)
        stdscr.refresh()
        ch = stdscr.getch()
        if ch in (curses.KEY_ENTER, 10, 13):
            return filt
        elif ch == 27:  # Esc
            return ""
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            filt = filt[:-1]
        elif 32 <= ch < 127:
            filt += chr(ch)


def main():
    ap = argparse.ArgumentParser(
        description="TUI porovnání dvou adresářů s vimdiff po výběru souboru.")
    ap.add_argument("a", help="první adresář (A)")
    ap.add_argument("b", help="druhý adresář (B)")
    args = ap.parse_args()

    dir_a = Path(args.a)
    dir_b = Path(args.b)
    for d in (dir_a, dir_b):
        if not d.is_dir():
            print(f"Není adresář: {d}", file=sys.stderr)
            return 2

    def progress(done, total):
        sys.stdout.write(f"\rPorovnávám... {done}/{total}")
        sys.stdout.flush()

    entries = build_entries(dir_a, dir_b, progress)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()

    if not entries:
        print("Žádné soubory k porovnání.")
        return 0

    root = build_tree(entries)
    curses.wrapper(run_tui, dir_a, dir_b, root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
