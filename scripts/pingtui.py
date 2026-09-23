#!/usr/bin/env python3
"""TUI ping — pinguje více adres najednou a vykresluje tabulku odezev.

Sloupce tabulky = adresy, řádky = jednotlivé "ticky" (pořadová čísla pingu).
Každý nový ping přidá dolů nový řádek: buňka se objeví ihned po odeslání
packetu jako "pending" (…) a jakmile dorazí odpověď, zpětně se do ní dopíše
doba odezvy, chybová hláška, nebo timeout (po 10 s).

Použití:
    ./pingtui.py 8.8.8.8 1.1.1.1 example.com
    ./pingtui.py -i 2 -t 3 8.8.8.8 seznam.cz
    ./pingtui.py dns:google.com 'dns:seznam.cz@10.0.0.1:53'
    ./pingtui.py '8.8.8.8@ssh gw' 'dns:google.com@1.1.1.1@ssh gw'
    ./pingtui.py --json 8.8.8.8         # JSON událost za akci (pro remote)

Specifikace cíle (dělí se vždy prvním @ zleva):
    adresa                       lokální ICMP ping
    v4:jméno / v6:jméno          vynutí IPv4/IPv6 překlad jména
                                 (default preferuje stejně jako systém)
    cíl^N                        pingat N-tý hop cesty k cíli (jako traceroute;
                                 hop se dohledává periodicky jako překlad)
    _gateway                     ping na default gateway (z routovací tabulky)
    gateway:<iface>              default gateway ("via") skrz daný interface
    if:<iface>[#n]               n-tá (default první) IP adresa interface
    if4:<iface>[#n]:<konec>      síťový prefix n-té IPv4 adresy interface
                                 + doplněný konec (např. if4:w:21)
    if6:<iface>[#n]:<konec>      totéž pro IPv6 (např. if6:wg0:10:1)
    adresa@<příkaz>              remote: `<příkaz> pingtui --json adresa`
    adresa@@<příkaz>             jméno přeloží hlavní proces (mimo namespace),
                                 remote pinguje už hotovou IP; při změně
                                 překladu se remote restartuje s novou IP
    dns:jméno                    test DNS resolve (systémový resolver)
    dns:jméno@server[:port]      test DNS proti konkrétnímu serveru
    dns:jméno@server@<příkaz>    totéž, spuštěné remote
    Stejný @<příkaz> u více cílů = jedno sdílené spojení.
    Per-host parametry čárkami hned za cílem (před prvním @):
    cíl,i=0.2,t=2,w=5,r=30,label=doma — i/interval (frekvence pingu),
    t/timeout, w/max-wait, r/resolve-interval, label (název sloupce);
    krátký i dlouhý název. Řádky tabulky běží na nejmenším intervalu,
    pomalejší hosty nechávají mezilehlé buňky prázdné.
    Jméno DNS dotazu může obsahovat wildcards (expandují se per dotaz):
    %i = sekvenční číslo, %5h = 5 znaků hashe seq, %5r = 5 náhodných znaků,
    %5c = 5 znaků náhodného identifikátoru session (stejný po celý běh),
    %% = literál % — např. dns:%5r.example.com obchází DNS cache.

Ovládání:
    q / Esc     konec
    šipky ↑/↓   posun po řádcích (jinak drží nejnovější)
    end         zpět na živý konec
"""

import argparse
import asyncio
import curses
import hashlib
import ipaddress
import json
import os
import random
import re
import shlex
import socket
import struct
import sys
import time
from dataclasses import dataclass, field

# ── stav jednoho pingu ────────────────────────────────────────────────────────

PENDING, OK, ERROR, TIMEOUT = "pending", "ok", "error", "timeout"


@dataclass
class Ping:
    seq: int
    status: str = PENDING
    rtt: float | None = None       # ms
    msg: str = ""                  # krátký text chyby do buňky
    detail: str = ""               # plný popis negativní odpovědi
    ttl: int | None = None         # u DNS: zbývající platnost odpovědi (s)
    created: float = 0.0           # čas odeslání (monotonic)
    wall: float = 0.0              # čas odeslání (wall clock, pro sloupec HH:MM:SS)


@dataclass
class PingResult:
    """Výsledek jedné sondy (nezávislý na tom, kdo ji provedl)."""
    status: str
    rtt: float | None = None       # ms
    msg: str = ""
    detail: str = ""
    ttl: int | None = None         # u DNS: TTL odpovědi (s)


@dataclass
class Note:
    """Informační řádek vložený do tabulky (resolve / reverse lookup)."""
    seq: int                       # za který tick se řadí
    kind: str                      # "resolve" | "reverse"
    text: str


@dataclass(eq=False)               # identita objektu (hashovatelný jako klíč)
class Host:
    addr: str
    label: str = ""                # zobrazovaný název sloupce (default = addr)
    spec: str = ""                 # plná specifikace (JSON id; default = addr)
    remote_spec: str = ""          # specifikace předávaná remote instanci
    transport: str = ""            # neprázdné = remote (přes tento příkaz, např. "ssh h")
    family: int = 0                # 0 = dle systému, jinak AF_INET/AF_INET6
    gateway: bool = False          # cíl je default gateway z routovací tabulky
    gw_iface: str = ""             # omezit na routy skrz tento interface
    ifspec: str = ""               # if*: cíl odvozený z adresy interface
    if_index: int = 1              # #n = n-tá adresa interface (1-based)
    if_tail: str = ""              # konec doplněný za síťový prefix adresy
    hop: int = 0                   # ^N: pingat N-tý hop cesty k cíli
    # per-host přenastavení (None = zdědit globální hodnotu z CLI)
    interval: float | None = None      # i= frekvence pingu
    timeout: float | None = None       # t= práh timeoutu/ztráty
    max_wait: float | None = None      # w= max čekání na pozdní odpověď
    resolve_int: float | None = None   # r= frekvence resolve/reverse
    params_str: str = ""           # kanonický ",k=v,…" (cestuje na remote)
    local_resolve: bool = False    # @@: jméno přeloží hlavní proces, remote
                                   # dostane už hotovou IP
    prober: object = None          # lokální sonda (IcmpProbe/DnsProbe); remote: None
    pings: dict[int, Ping] = field(default_factory=dict)
    sent: int = 0
    recv: int = 0
    lost: int = 0                  # finálně ztracené (ERROR + TIMEOUT)
    neg: int = 0                   # počet pingů s detailem (pro počítání řádků)
    notes: dict[int, list[Note]] = field(default_factory=dict)
    last_resolve: str = ""         # poslední → hodnota (do hlavičky)
    last_reverse: str = ""         # poslední ← hodnota (do hlavičky)
    nnotes: int = 0                # celkem note řádků (pro počítání řádků)
    note_w: int = 0                # nejdelší note text (pro šířku sloupce)
    last_seq: int = 0              # nejvyšší seq vč. not (pro výšku tabulky)
    last_ping: int = 0             # nejvyšší seq skutečného pingu (offset feederu)
    rtt_sum: float = 0.0
    rtt_min: float | None = None
    rtt_max: float | None = None
    # dosud nedořešené pingy (pro O(1) statistiky bez procházení historie)
    inflight: set = field(default_factory=set)

    def __post_init__(self):
        if not self.label:
            self.label = self.addr
        if not self.spec:
            self.spec = self.addr
        if not self.remote_spec:
            self.remote_spec = self.addr

    def add(self, p: "Ping") -> None:
        """Zaeviduj odeslaný ping (pending)."""
        self.pings[p.seq] = p
        self.sent += 1
        self.inflight.add(p.seq)
        if p.seq > self.last_seq:
            self.last_seq = p.seq
        if p.seq > self.last_ping:
            self.last_ping = p.seq

    def resolve(self, p: "Ping") -> None:
        """Zaeviduj výsledek (p.status už je nastaven)."""
        self.inflight.discard(p.seq)
        if p.status == OK and p.rtt is not None:
            self.recv += 1
            self.rtt_sum += p.rtt
            self.rtt_min = p.rtt if self.rtt_min is None else min(self.rtt_min, p.rtt)
            self.rtt_max = p.rtt if self.rtt_max is None else max(self.rtt_max, p.rtt)
        else:
            self.lost += 1
        if p.detail:
            self.neg += 1

    def note(self, seq: int, kind: str, text: str) -> Note:
        """Vloží/aktualizuje note buňku (jedna per (seq, kind)).
        Kind "err:*" se kreslí přes celý řádek → nepočítá se do šířky sloupce."""
        if not kind.startswith("err:"):
            self.note_w = max(self.note_w, len(text))
        lst = self.notes.setdefault(seq, [])
        for n in lst:
            if n.kind == kind:
                n.text = text
                return n
        n = Note(seq, kind, text)
        lst.append(n)
        self.nnotes += 1
        if seq > self.last_seq:
            self.last_seq = seq
        return n

    @property
    def avg(self) -> float | None:
        return self.rtt_sum / self.recv if self.recv else None

    @property
    def tx(self) -> float:
        """Efektivní práh timeoutu (per-host t=, jinak globální -t)."""
        return self.timeout if self.timeout is not None else TIMEOUT_X

    @property
    def loss(self) -> float:
        """Ztráta v % jen z pingů, které už dorazily, nebo jsou na cestě
        déle než práh timeoutu. Čerstvé pending (které ještě mají čas dorazit)
        se nezapočítávají, aby ztráta zbytečně neposkakovala. O(inflight)."""
        now = time.monotonic()
        old_pending = sum(1 for s in self.inflight
                          if (p := self.pings.get(s)) and now - p.created >= self.tx)
        counted = self.recv + self.lost + old_pending
        lost = self.lost + old_pending
        return 0.0 if counted == 0 else 100.0 * lost / counted


# ── pingání ───────────────────────────────────────────────────────────────────

_TIME_RE = re.compile(r"time[=<]\s*([\d.]+)\s*ms")


def _notify(state: "dict | None", event: str, host: Host, p: Ping) -> None:
    """Oznámí změnu: probudí renderer (dirty) a/nebo vyšle JSON událost."""
    if not state:
        return
    dirty = state.get("dirty")
    if dirty:
        dirty.set()
    emit = state.get("emit")
    if emit:
        obj = {"event": event, "host": host.spec, "seq": p.seq, "t": time.time()}
        if event == "result":
            obj.update(status=p.status, rtt=p.rtt, msg=p.msg, detail=p.detail,
                       ttl=p.ttl)
        emit(obj)


def _set_note(state: "dict | None", host: Host, seq: int, kind: str,
              text: str) -> None:
    """Vloží/aktualizuje note buňku a oznámí změnu (dirty + JSON událost).

    Notes se kreslí jako sloupcově zarovnané řádky: jeden řádek tabulky na
    (seq, kind) sdílený všemi cíli; registry v state počítá tyto řádky."""
    note = host.note(seq, kind, text)
    if kind == "resolve":          # aktuální stav překladu do hlavičky
        host.last_resolve = text
    elif kind == "reverse":
        host.last_reverse = text
    if not state:
        return
    # registry řádků: {seq: {kind: max délka buňky}} + histogram délek (nlh),
    # aby šel počet zalomených řádků spočítat v O(1) při každém překreslení
    reg = state.setdefault("noterows", {})
    kinds = reg.setdefault(seq, {})
    length = 0 if kind.startswith("err:") else len(text)
    nlh = state.setdefault("nlh", {})
    cur = kinds.get(kind)
    if cur is None:
        kinds[kind] = length
        nlh[length] = nlh.get(length, 0) + 1
        state["nnoterows"] = state.get("nnoterows", 0) + 1
    elif length > cur:
        nlh[cur] -= 1
        nlh[length] = nlh.get(length, 0) + 1
        kinds[kind] = length
    dirty = state.get("dirty")
    if dirty:
        dirty.set()
    emit = state.get("emit")
    if emit:
        emit({"event": "note", "host": host.spec, "seq": note.seq,
              "kind": note.kind, "text": note.text, "t": time.time()})


async def one_ping(host: Host, seq: int, state: "dict | None" = None,
                   delay: float = 0.0) -> None:
    """Odešle jeden ICMP echo a zpětně doplní výsledek do host.pings[seq].

    Ping běží až do MAX_WAIT, aby zachytil i pozdní odpověď (kterou pak
    v tabulce přepíšeme z timeoutu na skutečnou dobu). O tom, kdy se ping
    vizuálně označí za timeout, rozhoduje práh X (TIMEOUT_X) při vykreslování.

    `delay` posune samotné odeslání (staggering) — pending se objeví až
    v okamžiku, kdy packet skutečně odchází, ne dřív.
    """
    if delay:
        await asyncio.sleep(delay)
        if state and state["quit"]:
            return
    # Bez cílové IP žádný packet neodchází → žádná pending buňka a nic se
    # nezapočítává do "odesláno". Chvíli počkáme (≤ interval), jestli překlad
    # nedoběhne; jinak se tento tick u cíle přeskočí (důvod je v note řádku).
    max_wait = host.max_wait if host.max_wait is not None else MAX_WAIT
    itv = (host.interval if host.interval is not None
           else (state or {}).get("interval", 1.0))
    err = await host.prober.prepare(min(max_wait, itv))
    if err is not None or (state and state["quit"]):
        return
    p = Ping(seq=seq, status=PENDING, created=time.monotonic(), wall=time.time())
    host.add(p)                    # pending buňka až v okamžiku odeslání
    _notify(state, "send", host, p)

    try:
        try:
            res = await host.prober.probe(max_wait, seq)
        except Exception as e:  # noqa: BLE001
            res = PingResult(ERROR, msg=str(e)[:40])
        p.status, p.rtt, p.msg = res.status, res.rtt, res.msg
        p.detail, p.ttl = res.detail, res.ttl
        host.resolve(p)            # odpověď dorazila (klidně i po X)
    finally:
        _notify(state, "result", host, p)


_ICMP_ERR_RE = re.compile(
    r"(unreachable|no route|network is|host is down|redirect|prohibited|"
    r"expired in transit|truncated)", re.I)
_DNS_ERR_RE = re.compile(
    r"(name or service|not known|unknown host|temporary failure|"
    r"no address)", re.I)


def _icmp_error(text: str) -> str:
    """Vrátí konkrétní ICMP/DNS chybovou hlášku, nebo '' když žádná není.

    Rozliší rychlé chyby (Destination Host Unreachable apod.) od skutečného
    timeoutu, který se v ping výstupu projeví jen jako '100% packet loss'.
    """
    for line in text.splitlines():
        s = line.strip()
        if _DNS_ERR_RE.search(s):
            return "neznámé jméno"
        m = _ICMP_ERR_RE.search(s)
        if m:
            idx = s.find("Destination")          # typicky "Destination ... Unreachable"
            start = idx if idx >= 0 else m.start()
            return s[start:start + 26]
    return ""


def _error_detail(text: str) -> str:
    """Vrátí co nejpodrobnější řádek s popisem negativní odpovědi (nezkrácený)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        low = ln.lower()
        if (_DNS_ERR_RE.search(ln) or _ICMP_ERR_RE.search(ln)
                or "error" in low or ln.startswith("ping:")
                or ln.startswith("From ")):
            return ln
    # fallback: poslední řádek, který není souhrnná statistika
    for ln in reversed(lines):
        if "packet" not in ln.lower() and "statistics" not in ln.lower():
            return ln
    return lines[-1] if lines else "neznámá chyba"


def _first_error(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        low = line.lower()
        if any(k in low for k in ("unknown", "unreachable", "failure", "name", "error")):
            return line[:40]
    return (text.strip().splitlines() or ["chyba"])[0][:40]


# ── pingery: nativní ICMP socket (default) + subprocess fallback ───────────────

DEFAULT_CMD = "ping -n -c 1 -W {w} {host}"


def _icmp_checksum(data: bytes) -> int:
    if len(data) % 2:
        data += b"\x00"
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    return ~s & 0xFFFF


def _build_echo(ident: int, seq: int, payload: bytes, echo_type: int = 8,
                checksum: bool = True) -> bytes:
    """Sestaví ICMP/ICMPv6 echo request. U ICMPv6 (checksum=False) doplní
    kontrolní součet jádro (potřebuje pseudo-hlavičku), posíláme tedy 0."""
    head = struct.pack("!BBHHH", echo_type, 0, 0, ident, seq)
    chk = _icmp_checksum(head + payload) if checksum else 0
    return struct.pack("!BBHHH", echo_type, 0, chk, ident, seq) + payload


# ICMP „destination unreachable" (type 3) kódy → čitelný popis
_UNREACH = {
    0: "Network Unreachable", 1: "Host Unreachable", 2: "Protocol Unreachable",
    3: "Port Unreachable", 4: "Fragmentation needed", 5: "Source route failed",
    6: "Network unknown", 7: "Host unknown", 9: "Network prohibited",
    10: "Host prohibited", 13: "Communication prohibited",
}


class SubprocessPinger:
    """Fallback: spustí externí `ping` (jeden proces na ping). Šablona příkazu
    může obsahovat {host} a {w} (timeout v s)."""

    def __init__(self, cmd_template: str = DEFAULT_CMD):
        self.cmd_template = cmd_template

    async def ping(self, addr: str, max_wait: float) -> PingResult:
        w = max(1, int(max_wait))
        argv = [tok.format(host=addr, w=w) for tok in shlex.split(self.cmd_template)]
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT)
        except FileNotFoundError:
            return PingResult(ERROR, msg="ping nenalezen")
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=max_wait + 1)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return PingResult(TIMEOUT)
        text = out.decode(errors="replace")
        m = _TIME_RE.search(text)
        err = _icmp_error(text)
        if proc.returncode == 0 and m:
            return PingResult(OK, rtt=float(m.group(1)))
        if err:
            return PingResult(ERROR, msg=err, detail=_error_detail(text))
        if "100% packet loss" in text:
            return PingResult(TIMEOUT)
        return PingResult(ERROR, msg=_first_error(text), detail=_error_detail(text))


class NativePinger:
    """Nativní ICMP/ICMPv6 echo přes sdílené sockety a asyncio — bez spouštění
    procesů. Podporuje IPv4 i IPv6 (dual-stack). Zkusí neprivilegovaný
    SOCK_DGRAM (Linux ping_group_range), jinak SOCK_RAW (root). Rodinu adresy
    vybere z getaddrinfo; co neumí (nebo gaierror) → `fallback`."""

    # per-rodinná konfigurace ICMP vs ICMPv6
    _FAM = {
        socket.AF_INET: dict(
            proto=socket.IPPROTO_ICMP, echo=8, reply=0, unreach=3, timeexc=11,
            checksum=True),
        socket.AF_INET6: dict(
            proto=getattr(socket, "IPPROTO_ICMPV6", 58), echo=128, reply=129,
            unreach=1, timeexc=3, checksum=False),
    }

    def __init__(self, fallback: "SubprocessPinger | None" = None):
        self.fallback = fallback
        self.socks: dict[int, tuple[socket.socket, bool]] = {}   # family → (sock, is_raw)
        self.ident = os.getpid() & 0xFFFF
        self.seq = 0
        self.pending: dict[int, asyncio.Future] = {}
        self.loop: asyncio.AbstractEventLoop | None = None

    def _open(self, family: int) -> tuple[socket.socket, bool]:
        proto = self._FAM[family]["proto"]
        try:
            s = socket.socket(family, socket.SOCK_DGRAM, proto)
            raw = False
        except (PermissionError, OSError):
            s = socket.socket(family, socket.SOCK_RAW, proto)   # může vyhodit
            raw = True
        s.setblocking(False)
        return s, raw

    def start(self) -> None:
        """Otevře IPv4 i IPv6 ICMP socket (co jde) a zaregistruje čtečky.
        Vyhodí, pokud nejde otevřít ani jeden (→ volající sáhne po fallbacku)."""
        self.loop = asyncio.get_running_loop()
        last = None
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                s, raw = self._open(family)
            except (PermissionError, OSError) as e:
                last = e
                continue
            self.socks[family] = (s, raw)
            self.loop.add_reader(
                s.fileno(),
                lambda s=s, fam=family, raw=raw: self._readable(s, fam, raw))
        if not self.socks:
            raise last or OSError("nelze otevřít ICMP socket")

    def close(self) -> None:
        for s, _raw in self.socks.values():
            try:
                self.loop.remove_reader(s.fileno())
            except Exception:  # noqa: BLE001
                pass
            s.close()
        self.socks = {}

    def _readable(self, sock: socket.socket, family: int, raw: bool) -> None:
        while True:
            try:
                data, _addr = sock.recvfrom(2048)
            except (BlockingIOError, InterruptedError):
                return
            except OSError:
                return
            self._dispatch(data, family, raw)

    def _dispatch(self, data: bytes, family: int, raw: bool) -> None:
        cfg = self._FAM[family]
        icmp = data
        if family == socket.AF_INET and raw:     # jen IPv4 SOCK_RAW nese IP hlavičku
            if len(data) < 20:
                return
            icmp = data[(data[0] & 0x0F) * 4:]
        if len(icmp) < 8:
            return
        typ = icmp[0]
        if typ == cfg["reply"]:                  # echo reply
            _ident, seq = struct.unpack("!HH", icmp[4:8])
            self._resolve(seq, ("ok",))
        elif typ in (cfg["unreach"], cfg["timeexc"]):
            orig = icmp[8:]                      # vnořený původní datagram
            oicmp = None
            if family == socket.AF_INET:
                if len(orig) >= 28:
                    oicmp = orig[(orig[0] & 0x0F) * 4:][:8]
            elif len(orig) >= 48:                # IPv6 hlavička je pevných 40 B
                oicmp = orig[40:48]
            if oicmp and len(oicmp) >= 8 and oicmp[0] == cfg["echo"]:
                _i, oseq = struct.unpack("!HH", oicmp[4:8])
                kind = "unreachable" if typ == cfg["unreach"] else "timeexceeded"
                self._resolve(oseq, (kind, icmp[1]))

    def _resolve(self, seq: int, result: tuple) -> None:
        fut = self.pending.get(seq)
        if fut and not fut.done():
            fut.set_result(result)

    async def ping(self, addr: str, max_wait: float) -> PingResult:
        loop = self.loop
        try:
            infos = await loop.getaddrinfo(addr, None, type=socket.SOCK_DGRAM)
        except socket.gaierror:
            if self.fallback:
                return await self.fallback.ping(addr, max_wait)
            return PingResult(ERROR, msg="neznámé jméno",
                              detail=f"ping: {addr}: Name or service not known")
        chosen = next(((fam, sa) for fam, _t, _p, _c, sa in infos
                       if fam in self.socks), None)
        if not chosen:                           # rodinu neumíme (chybí socket)
            if self.fallback:
                return await self.fallback.ping(addr, max_wait)
            return PingResult(ERROR, msg="nepodporovaná adresa",
                              detail=f"{addr}: chybí ICMP socket pro tuto rodinu")
        family, sa = chosen
        cfg = self._FAM[family]
        sock, _raw = self.socks[family]
        self.seq = seq = (self.seq + 1) & 0xFFFF
        pkt = _build_echo(self.ident, seq, b"pingtui-" + struct.pack("!H", seq),
                          echo_type=cfg["echo"], checksum=cfg["checksum"])
        fut = loop.create_future()
        self.pending[seq] = fut
        t0 = loop.time()
        try:
            sock.sendto(pkt, sa)                 # sa nese i scope-id (link-local)
            result = await asyncio.wait_for(fut, timeout=max_wait)
        except asyncio.TimeoutError:
            return PingResult(TIMEOUT)
        except OSError as e:                      # např. Network is unreachable
            msg = e.strerror or str(e)
            return PingResult(ERROR, msg=msg[:26], detail=f"{addr}: {msg}")
        finally:
            self.pending.pop(seq, None)
        rtt = (loop.time() - t0) * 1000.0
        if result[0] == "ok":
            return PingResult(OK, rtt=rtt)
        if result[0] == "unreachable":
            desc = _UNREACH.get(result[1], f"Unreachable (code {result[1]})")
            return PingResult(ERROR, msg=desc[:26],
                              detail=f"{addr}: ICMP Destination {desc}")
        return PingResult(ERROR, msg="TTL vypršel",
                          detail=f"{addr}: ICMP Time Exceeded")


def build_pinger(subprocess_only: bool, cmd_template: str):
    """Sestaví pinger: nativní ICMP (default) s fallbackem na subprocess."""
    sub = SubprocessPinger(cmd_template)
    if subprocess_only:
        return sub
    native = NativePinger(fallback=sub)
    try:
        native.start()
    except (PermissionError, OSError):
        return sub                           # ICMP socket nelze otevřít
    return native


PINGER = SubprocessPinger()   # výchozí; přenastaví se v amain() dle argumentů


# ── sondy: ICMP ping a DNS resolve test ───────────────────────────────────────

def _is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def _compact_ip(s: str) -> str:
    """Kanonický co nejkratší zápis IP (IPv6 s `::`); ne-IP vrací beze změny."""
    try:
        return ipaddress.ip_address(s).compressed
    except ValueError:
        return s


_RTF_GATEWAY = 0x2


def _gw4(iface: str) -> list[tuple[int, str]]:
    """IPv4 default routy z /proc/net/route → [(metrika, via-adresa)]."""
    out = []
    try:
        with open("/proc/net/route") as f:
            next(f)                                        # hlavička
            for line in f:
                p = line.split()
                if len(p) < 8 or p[1] != "00000000":       # jen default
                    continue
                if not int(p[3], 16) & _RTF_GATEWAY:
                    continue
                if iface and p[0] != iface:
                    continue
                gw = socket.inet_ntoa(struct.pack("<L", int(p[2], 16)))
                out.append((int(p[6]), gw))
    except OSError:
        pass
    return out


def _gw6(iface: str) -> list[tuple[int, str]]:
    """IPv6 default routy z /proc/net/ipv6_route → [(metrika, via-adresa)]."""
    out = []
    try:
        with open("/proc/net/ipv6_route") as f:
            for line in f:
                p = line.split()
                if len(p) < 10 or p[0] != "0" * 32 or p[1] != "00":
                    continue                               # jen default (::/0)
                if not int(p[8], 16) & _RTF_GATEWAY:
                    continue
                if iface and p[9] != iface:
                    continue
                gw = socket.inet_ntop(socket.AF_INET6, bytes.fromhex(p[4]))
                out.append((int(p[5], 16), gw))
    except OSError:
        pass
    return out


def _iface_exists(iface: str) -> bool:
    """Existence interface: /sys/class/net, s fallbackem na /proc/net/dev."""
    if os.path.isdir("/sys/class/net"):
        return os.path.exists(f"/sys/class/net/{iface}")
    try:
        with open("/proc/net/dev") as f:
            return any(line.split(":", 1)[0].strip() == iface
                       for line in f if ":" in line)
    except OSError:
        return True                    # nelze zjistit → nechme rozhodnout routy


def _gateway_lookup(iface: str, family: int) -> tuple[str | None, str]:
    """Najde default gateway ("via" adresu) v routovacích tabulkách.
    `iface` omezí na routy skrz daný interface; family 0 preferuje IPv4.
    Při více routách vyhrává nejnižší metrika.

    Vrací (ip, "") při úspěchu, jinak (None, detailní důvod selhání)."""
    if iface and not _iface_exists(iface):
        return None, f"interface {iface} neexistuje"
    routes = []
    if family in (0, socket.AF_INET):
        routes = _gw4(iface)
    if not routes and family in (0, socket.AF_INET6):
        routes = _gw6(iface)
    if routes:
        return min(routes)[1], ""
    famtxt = {0: "", socket.AF_INET: "IPv4 ",
              socket.AF_INET6: "IPv6 "}[family]
    if iface:
        state = ""
        try:
            with open(f"/sys/class/net/{iface}/operstate") as f:
                oper = f.read().strip()
            if oper not in ("up", "unknown"):
                state = f", interface je {oper}"
        except OSError:
            pass
        return None, f"{iface}: bez {famtxt}default routy{state}"
    return None, f"bez {famtxt}default routy"


async def _iface_addrs(iface: str) -> tuple[list[tuple[int, str, int]], str]:
    """Adresy interface via `ip -o addr show` → ([(family, addr, plen)], err)."""
    if not _iface_exists(iface):
        return [], f"interface {iface} neexistuje"
    try:
        proc = await asyncio.create_subprocess_exec(
            "ip", "-o", "addr", "show", "dev", iface,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, err = await proc.communicate()
    except FileNotFoundError:
        return [], "příkaz 'ip' nenalezen"
    if proc.returncode != 0:
        return [], (err.decode(errors="replace").strip().splitlines() or
                    [f"ip addr selhalo ({proc.returncode})"])[0]
    addrs = []
    for line in out.decode(errors="replace").splitlines():
        p = line.split()
        for i, tok in enumerate(p):
            if tok in ("inet", "inet6") and i + 1 < len(p):
                a, _, pl = p[i + 1].partition("/")
                fam = socket.AF_INET if tok == "inet" else socket.AF_INET6
                dflt = 32 if fam == socket.AF_INET else 128
                addrs.append((fam, a.split("%")[0], int(pl) if pl else dflt))
                break
    return addrs, ""


def _parse_tail(tail: str, family: int) -> int:
    """Konec adresy → číselná hodnota: v4 "1.21" po oktetech, v6 "10:1" po
    16bit skupinách. Vyhodí ValueError při neplatném zápisu."""
    if family == socket.AF_INET:
        value = 0
        for part in tail.split("."):
            v = int(part)
            if not 0 <= v <= 255:
                raise ValueError(part)
            value = value * 256 + v
        return value
    value = 0
    for part in tail.split(":"):
        v = int(part, 16)
        if not 0 <= v <= 0xFFFF:
            raise ValueError(part)
        value = value * 0x10000 + v
    return value


_FROM_RE = re.compile(r"^From (\S+)", re.M)


async def _hop_probe(target: str, ttl: int, max_wait: float
                     ) -> tuple[str, str]:
    """Jedna TTL-limitovaná sonda. Vrací (druh, data):
    ("exceeded", ip-routeru) / ("reply", "") / ("silent", "") / ("error", txt)."""
    cmd = ["ping", "-n", "-c", "1", "-t", str(ttl),
           "-W", str(max(1, int(max_wait))), target]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT)
        out, _ = await asyncio.wait_for(proc.communicate(),
                                        timeout=max_wait + 2)
    except FileNotFoundError:
        return "error", "ping nenalezen"
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return "silent", ""
    text = out.decode(errors="replace")
    if "xceeded" in text:              # Time to live exceeded / Hop limit
        m = _FROM_RE.search(text)
        if m:
            ip = m.group(1)
            if ip.endswith(":") and not ip.endswith("::"):
                ip = ip[:-1]           # "From 10.0.0.1:" varianta iputils
            return "exceeded", ip
    if proc.returncode == 0 and _TIME_RE.search(text):
        return "reply", ""
    err = _icmp_error(text)
    if err:
        return "error", err
    return "silent", ""


async def _hop_lookup(target: str, n: int, max_wait: float = 2.0
                      ) -> tuple[str | None, str, str]:
    """N-tý hop cesty k `target` (jako traceroute): ICMP echo s TTL=n,
    adresa routeru z Time Exceeded. Když s TTL=n odpoví přímo cíl, je cíl
    hopem N (pokud není blíž — ověří se sondou s TTL=n-1).

    Vrací (ip, "", "") při úspěchu, jinak (None, detailní důvod, značka).
    Značka != "" u dvou běžných stavů trasy, které se nekreslí jako chybový
    řádek, ale kompaktně do resolve tabulky: "mlčí" (hop neposílá Time
    Exceeded) a "mimo" (hop je za koncem cesty)."""
    kind, data = await _hop_probe(target, n, max_wait)
    if kind == "exceeded":
        return data, "", ""
    if kind == "error":
        return None, f"hop {n}: {data}", ""
    if kind == "silent":
        return None, f"hop {n} neodpovídá", "mlčí"
    # cíl odpověděl echem: je vzdálen ≤ n hopů. Hop n existuje (= cíl sám)
    # jen pokud cíl není blíž — sonda s TTL=n-1 nesmí dostat echo reply.
    if n > 1:
        kind2, _ = await _hop_probe(target, n - 1, max_wait)
        if kind2 == "reply":
            return None, (f"cíl odpověděl už s TTL={n - 1} — cesta je "
                          f"kratší než {n} hopů"), "mimo"
    return target, "", ""              # cíl je přesně na hopu N


async def _if_lookup(host: "Host") -> tuple[str | None, str]:
    """Vyhodnotí if*: cíl: n-tá adresa interface, případně síťový prefix
    z ní + doplněný konec. Vrací (ip, "") nebo (None, detailní důvod)."""
    addrs, err = await _iface_addrs(host.ifspec)
    if err:
        return None, err
    fam = host.family
    if fam:
        addrs = [a for a in addrs if a[0] == fam]
    if not addrs:
        famtxt = {socket.AF_INET: "IPv4 ", socket.AF_INET6: "IPv6 ",
                  0: ""}[fam]
        return None, f"{host.ifspec}: žádná {famtxt}adresa"
    if host.if_index > len(addrs):
        return None, (f"{host.ifspec}: má jen {len(addrs)} adres, "
                      f"požadována #{host.if_index}")
    afam, addr, plen = addrs[host.if_index - 1]
    if not host.if_tail:
        return addr, ""
    try:
        value = _parse_tail(host.if_tail, afam)
    except ValueError:
        return None, f"neplatný konec {host.if_tail!r}"
    bits = 32 if afam == socket.AF_INET else 128
    if plen < bits and value >= (1 << (bits - plen)):
        return None, f"konec {host.if_tail!r} se nevejde do /{plen}"
    if plen == bits:
        return None, (f"{addr}/{plen} nemá hostovou část, "
                      f"konec nelze doplnit")
    net = ipaddress.ip_interface(f"{addr}/{plen}").network
    return str(net.network_address + value), ""


class IcmpProbe:
    """Lokální ICMP sonda — deleguje na sdílený PINGER.

    Jmenné cíle se NEresolvují při každém pingu: resolver_task drží
    v `self.ip` poslední úspěšný překlad (obnovovaný každých pár sekund)
    a pinguje se vždy tato cachovaná IP."""

    def __init__(self, addr: str, family: int = 0, force_resolve: bool = False):
        self.addr = addr
        self.family = family           # 0 = dle systému, jinak AF_INET/AF_INET6
        # force_resolve: i IP literál musí projít resolverem (např. ^N hop)
        self.ip: str | None = (_compact_ip(addr)
                               if _is_ip(addr) and not force_resolve else None)
        self.fail = ""                 # detailní důvod posledního selhání resolve
        self.ready = asyncio.Event()
        if self.ip:
            self.ready.set()

    async def prepare(self, wait: float) -> str | None:
        """Počká (max `wait` s) na použitelnou cílovou IP. Vrátí None, když
        lze pingat, jinak důvod, proč packet nemůže odejít."""
        if self.ip is None:
            try:
                await asyncio.wait_for(self.ready.wait(), timeout=wait)
            except asyncio.TimeoutError:
                pass
        if self.ip is None:
            return self.fail or "překlad zatím nedoběhl"
        return None

    async def probe(self, max_wait: float, seq: int = 0) -> PingResult:
        if self.ip is None:                    # pojistka; hlídá už prepare()
            return PingResult(ERROR, msg="bez překladu",
                              detail=f"{self.addr}: {self.fail or 'překlad nedoběhl'}")
        return await PINGER.ping(self.ip, max_wait)


async def resolver_task(host: Host, probe: IcmpProbe, interval: float,
                        state: dict) -> None:
    """Periodicky (interval s) překládá jméno na IP. Úspěch → aktualizuje
    probe.ip a vloží do tabulky note řádky: resolve výsledek + (async)
    reverse lookup. Selhání/pomalý běh → dál se používá starý překlad."""
    loop = asyncio.get_running_loop()
    static_ip = probe.ip is not None           # cíl zadaný přímo IP adresou

    async def _next_round() -> None:
        """Čeká na další kolo překladu: klávesa 'r' (reresolve event) budí
        okamžitě; interval > 0 navíc obnovuje periodicky, 0 = jen ručně."""
        ev = state.get("reresolve")
        try:
            if ev is None:
                await asyncio.sleep(interval if interval > 0 else 3600.0)
            elif interval > 0:
                await asyncio.wait_for(ev.wait(), timeout=interval)
            else:
                await ev.wait()
        except asyncio.TimeoutError:
            pass

    while not state["quit"]:
        if static_ip:
            # překlad není potřeba, ale reverzní lookup děláme i tak;
            # když se cílová IP nedostane do hlavičky (vlastní label nebo
            # remote přes @@), ukaž ji aspoň v resolve řádku
            seq = max(1, state.get("seq", 0))
            if host.label != probe.ip:
                _set_note(state, host, seq, "resolve", probe.ip)
            _set_note(state, host, seq, "reverse", "…")
            asyncio.create_task(_reverse_task(host, probe.ip, seq, state))
            await _next_round()
            continue
        why = ""
        if host.gateway:                       # via adresa z routovací tabulky
            ip, why = _gateway_lookup(host.gw_iface, probe.family)
        elif host.ifspec:                      # adresa odvozená z interface
            ip, why = await _if_lookup(host)
        else:
            try:
                infos = await loop.getaddrinfo(host.addr, None,
                                               family=probe.family,
                                               type=socket.SOCK_DGRAM)
                ip = infos[0][4][0]
            except (socket.gaierror, OSError) as e:
                ip = None                      # ponech dosavadní překlad
                why = e.strerror or str(e)
        mark = ""
        if ip and host.hop:                    # ^N: dohledej N-tý hop cesty
            ip, why, mark = await _hop_lookup(ip, host.hop)
        if ip:
            ip = _compact_ip(ip)               # IPv6 co nejkratším zápisem
            changed = probe.ip is not None and probe.ip != ip
            probe.ip = ip
            probe.fail = ""
            probe.ready.set()
            seq = max(1, state.get("seq", 0))
            mark = "*" if changed else ""      # * = překlad se změnil
            _set_note(state, host, seq, "resolve", f"{ip}{mark}")
            _set_note(state, host, seq, "reverse", "…")
            asyncio.create_task(_reverse_task(host, ip, seq, state))
        else:
            probe.fail = why
            seq = max(1, state.get("seq", 0))
            if mark:
                # běžný stav trasy (hop mlčí / je za koncem cesty):
                # kompaktní značka do resolve tabulky místo chybového řádku
                _set_note(state, host, seq, "resolve", mark)
            elif probe.ip is None:             # nemáme ani starý překlad →
                _set_note(state, host, seq, f"err:{host.spec}", why)  # celý řádek
        await _next_round()


async def _reverse_task(host: Host, ip: str, seq: int, state: dict) -> None:
    """Asynchronní reverse lookup — po dokončení přepíše svou buňku."""
    loop = asyncio.get_running_loop()
    try:
        name, _ = await loop.getnameinfo((ip, 0), socket.NI_NAMEREQD)
        text = name
    except (socket.gaierror, OSError):
        text = "(bez PTR)"
    _set_note(state, host, seq, "reverse", text)


_WILD_RE = re.compile(r"%(\d*)([ihrc%])")
_WILD_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
# identifikátor session: vygenerovaný jednou per běh, %Nc z něj bere prefix
_SESSION_ID = "".join(random.choices(_WILD_ALPHABET, k=32))


def _expand_name(template: str, seq: int) -> str:
    """Expanduje wildcards ve jméně DNS dotazu (per dotaz, dle seq):

      %i    sekvenční číslo dotazu
      %5h   5 znaků hashe sekvenčního čísla (deterministické, N volitelné)
      %5r   5 náhodných znaků (N volitelné, výchozí 5)
      %5c   5 znaků náhodného identifikátoru session (stejný po celý běh)
      %%    literál %

    Hodí se na obcházení DNS cache: dns:%5r.example.com se ptá pokaždé jinam;
    dns:%c-%i.example.com dovolí na straně serveru rozlišit session i dotaz.
    """
    def repl(m: "re.Match") -> str:
        n = int(m.group(1)) if m.group(1) else 5
        kind = m.group(2)
        if kind == "%":
            return "%"
        if kind == "i":
            return str(seq)
        if kind == "h":
            return hashlib.sha256(str(seq).encode()).hexdigest()[:n]
        if kind == "c":
            return _SESSION_ID[:n]
        return "".join(random.choices(_WILD_ALPHABET, k=n))    # 'r'

    return _WILD_RE.sub(repl, template)


_DNS_RCODE = {1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN", 4: "NOTIMP",
              5: "REFUSED"}
_dns_qid = [os.getpid() & 0xFFFF]


def _default_dns() -> str:
    """První nameserver z /etc/resolv.conf (cachovaně), jinak 8.8.8.8."""
    if not hasattr(_default_dns, "cached"):
        server = "8.8.8.8"
        try:
            with open("/etc/resolv.conf") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] == "nameserver":
                        server = parts[1]
                        break
        except OSError:
            pass
        _default_dns.cached = server
    return _default_dns.cached


def _build_dns_query(qid: int, name: str) -> bytes:
    head = struct.pack("!HHHHHH", qid, 0x0100, 1, 0, 0, 0)   # RD=1, 1 otázka
    q = b"".join(bytes([len(lb)]) + lb.encode("idna")
                 for lb in name.split(".") if lb) + b"\x00"
    return head + q + struct.pack("!HH", 1, 1)               # A, IN


def _dns_skip_name(buf: bytes, i: int) -> int:
    while i < len(buf):
        ln = buf[i]
        if ln == 0:
            return i + 1
        if ln & 0xC0 == 0xC0:                                # komprese: pointer
            return i + 2
        i += 1 + ln
    return i


def _parse_dns_reply(data: bytes, qid: int) -> "tuple[int, list[int]] | None":
    """Vrátí (rcode, [TTL odpovědí]), nebo None když reply nepatří k dotazu."""
    if len(data) < 12:
        return None
    rid, flags, qd, an, _ns, _ar = struct.unpack_from("!HHHHHH", data)
    if rid != qid or not flags & 0x8000:
        return None
    i = 12
    for _ in range(qd):                                      # přeskoč otázky
        i = _dns_skip_name(data, i) + 4
    ttls = []
    for _ in range(an):
        i = _dns_skip_name(data, i)
        if i + 10 > len(data):
            break
        _typ, _cls, ttl, rdlen = struct.unpack_from("!HHIH", data, i)
        ttls.append(ttl)
        i += 10 + rdlen
    return flags & 0xF, ttls


class DnsProbe:
    """DNS sonda: změří dobu resolve dotazu (A záznam) a TTL odpovědi.
    Používá vlastní UDP dotaz — server buď explicitní, nebo systémový.
    Jméno může obsahovat wildcards %i/%Nh/%Nr (viz _expand_name)."""

    def __init__(self, name: str, server: str | None = None, port: int = 53):
        self.name = name
        self.server = server
        self.port = port

    async def prepare(self, wait: float) -> str | None:
        return None                    # DNS sonda resolvuje sama — vždy ready

    async def probe(self, max_wait: float, seq: int = 0) -> PingResult:
        loop = asyncio.get_running_loop()
        server = self.server or _default_dns()
        name = _expand_name(self.name, seq) if "%" in self.name else self.name
        where = f"dns:{name}@{server}:{self.port}"
        _dns_qid[0] = qid = (_dns_qid[0] + 1) & 0xFFFF
        pkt = _build_dns_query(qid, name)
        family = socket.AF_INET6 if ":" in server else socket.AF_INET
        s = socket.socket(family, socket.SOCK_DGRAM)
        s.setblocking(False)
        try:
            s.connect((server, self.port))
            t0 = loop.time()
            s.send(pkt)
            deadline = t0 + max_wait
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    return PingResult(TIMEOUT)
                data = await asyncio.wait_for(loop.sock_recv(s, 4096),
                                              timeout=remaining)
                parsed = _parse_dns_reply(data, qid)
                if parsed is None:                     # cizí/poškozená odpověď
                    continue
                rtt = (loop.time() - t0) * 1000.0
                rcode, ttls = parsed
                if rcode:
                    name = _DNS_RCODE.get(rcode, f"rcode {rcode}")
                    return PingResult(ERROR, msg=name,
                                      detail=f"{where}: {name}")
                # NOERROR: TTL nejkratšího záznamu; bez záznamů (NODATA) None
                return PingResult(OK, rtt=rtt,
                                  ttl=min(ttls) if ttls else None)
        except asyncio.TimeoutError:
            return PingResult(TIMEOUT)
        except OSError as e:                           # ECONNREFUSED apod.
            msg = e.strerror or str(e)
            return PingResult(ERROR, msg=msg[:26], detail=f"{where}: {msg}")
        finally:
            s.close()


# ── parsování specifikace cíle: cíl[@dns-server[:port]][@transport] ───────────

_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$")


def _parse_hostport(s: str) -> "tuple[str, int] | None":
    """Vrátí (host, port), pokud `s` vypadá jako IP/jméno[:port]; jinak None."""
    if not s or " " in s:
        return None
    m = re.match(r"^\[([0-9A-Fa-f:]+)\](?::(\d+))?$", s)     # [v6]:port
    if m:
        return m.group(1), int(m.group(2) or 53)
    if s.count(":") >= 2:                                    # holá IPv6
        try:
            import ipaddress
            ipaddress.ip_address(s)
            return s, 53
        except ValueError:
            return None
    host, _, port = s.partition(":")
    if port and not port.isdigit():
        return None
    if _HOSTNAME_RE.match(host):
        return host, int(port) if port else 53
    return None


# per-host parametry: krátká zkratka i plný název → kanonické jméno pole Host
_PARAM_KEYS = {
    "i": "interval", "interval": "interval",
    "t": "timeout", "timeout": "timeout",
    "w": "max_wait", "max-wait": "max_wait", "max_wait": "max_wait",
    "r": "resolve_int", "resolve-interval": "resolve_int",
    "resolve_int": "resolve_int",
    "label": "label",
}


def _strip_trailing_params(spec: str) -> tuple[str, list[str]]:
    """Odloupne z KONCE specifikace per-host parametry `,k=v` (za transportem).
    Umožní tak psát parametry i na konec: `_gateway@@cmd,label=gw`. Odzobává
    odzadu, dokud poslední čárkou oddělený úsek je `známý-klíč=hodnota`.
    Vrací (spec bez koncových parametrů, [úseky k=v v původním pořadí])."""
    trailing: list[str] = []
    while (idx := spec.rfind(",")) >= 0:
        seg = spec[idx + 1:]
        k, eq, _v = seg.partition("=")
        if not eq or _PARAM_KEYS.get(k) is None:
            break
        trailing.append(seg)
        spec = spec[:idx]
    trailing.reverse()
    return spec, trailing


def _parse_params(head: str, spec: str,
                  extra: "list[str] | None" = None) -> tuple[str, dict, str]:
    """Oddělí z cílové části per-host parametry: `cíl,k=v,k=v…`. `extra` jsou
    další úseky `k=v` posbírané z konce specifikace (za transportem).
    Vrací (čistý cíl, {kanonický klíč: hodnota}, ",k=v,…" pro remote)."""
    parts = head.split(",")
    kv: dict = {}
    kept = []
    for part in parts[1:] + list(extra or []):
        k, eq, v = part.partition("=")
        if not eq:
            raise ValueError(f"parametr {part!r} nemá tvar klíč=hodnota "
                             f"(ve specifikaci {spec!r})")
        key = _PARAM_KEYS.get(k)
        if key is None:
            raise ValueError(f"neznámý parametr {k!r} (ve specifikaci {spec!r}); "
                             f"znám: i/interval, t/timeout, w/max-wait, "
                             f"r/resolve-interval, label")
        if key == "label":
            kv[key] = v
        else:
            try:
                val = float(v)
                # r=0 znamená „nepřekládat automaticky"; jinde 0 nedává smysl
                if val < 0 or (val == 0 and key != "resolve_int"):
                    raise ValueError
            except ValueError:
                raise ValueError(f"neplatná hodnota {v!r} parametru {k} "
                                 f"(ve specifikaci {spec!r})") from None
            kv[key] = val
        kept.append(f"{k}={v}")
    return parts[0], kv, ("," + ",".join(kept) if kept else "")


def parse_spec(spec: str) -> Host:
    """Rozparsuje specifikaci cíle na Host (bez probera — ten se přiřadí
    později, protože IcmpProbe potřebuje běžící PINGER).

    Formáty (dělí se vždy prvním @ zleva):
      8.8.8.8                    lokální ICMP ping
      8.8.8.8@ssh gw             ICMP ping spuštěný přes `ssh gw pingtui --json`
      dns:name                   DNS resolve test přes systémový resolver
      dns:name@1.2.3.4:53        DNS test proti konkrétnímu serveru
      dns:name@1.2.3.4@ssh gw    DNS test proti serveru, spuštěný remote
    """
    # per-host parametry ,k=v smí být u cíle (před prvním @) i na konci
    # specifikace (za transportem) — posbíráme je z obou míst
    body, tail_params = _strip_trailing_params(spec)
    head, sep, rest = body.partition("@")
    head, kv, params_str = _parse_params(head, spec, tail_params)
    label = kv.pop("label", "") or spec
    common = dict(label=label, spec=spec, params_str=params_str, **kv)
    if head.startswith("dns:"):
        name = head[4:]
        server, port, transport = None, 53, ""
        if sep:
            first, sep2, rest2 = rest.partition("@")
            hp = _parse_hostport(first)
            if hp:                                   # část za @ je DNS server
                server, port = hp
                transport = rest2 if sep2 else ""
            else:                                    # část za @ je transport
                transport = rest
        if transport.startswith("@"):                # @@ u dns: nemá význam
            transport = transport[1:]                # (sonda resolvuje sama)
        if server:
            srv = f"[{server}]" if ":" in server else server   # IPv6 → závorky
            remote_spec = f"dns:{name}{params_str}@{srv}:{port}"
        else:
            remote_spec = f"dns:{name}{params_str}"
        return Host(addr=name, remote_spec=remote_spec, transport=transport,
                    prober=None if transport else DnsProbe(name, server, port),
                    **common)
    # obyčejný ping: vše za prvním @ je transport; volitelný prefix v4:/v6:
    # vynutí rodinu překladu jména (default: preferuje se stejně jako systém)
    family = 0
    addr = head
    if head.startswith("v4:"):
        family, addr = socket.AF_INET, head[3:]
    elif head.startswith("v6:"):
        family, addr = socket.AF_INET6, head[3:]
    # cíl^N: pingat N-tý hop cesty k cíli (jako traceroute)
    hop = 0
    m = re.match(r"^(.+)\^(\d+)$", addr)
    if m:
        addr, hop = m.group(1), int(m.group(2))
    # _gateway / gateway:<iface>: cíl = default gateway z routovací tabulky
    gateway, gw_iface = False, ""
    if addr == "_gateway":
        gateway = True
    elif addr.startswith("gateway:"):
        gateway, gw_iface = True, addr[8:]
    # if4:iface:konec / if6:iface:konec / if:iface[#n]: cíl z adresy interface
    ifspec, if_index, if_tail = "", 1, ""
    m = re.match(r"^if([46]?):([^:#]+)(?:#(\d+))?(?::(.+))?$", addr)
    if m and not gateway:
        ifver, ifspec, idx, if_tail = m.groups()
        if_index = int(idx) if idx else 1
        if_tail = if_tail or ""
        if ifver == "4":
            family = socket.AF_INET
        elif ifver == "6":
            family = socket.AF_INET6
    transport = rest if sep else ""
    # dvojzavináč (cíl@@transport): překlad provede hlavní proces (mimo
    # namespace), remote instance dostane už hotovou IP adresu
    local_resolve = False
    if transport.startswith("@"):
        local_resolve, transport = True, transport[1:]
    return Host(addr=addr, remote_spec=head + params_str,   # vč. prefixu i parametrů
                transport=transport, family=family,
                gateway=gateway, gw_iface=gw_iface, local_resolve=local_resolve,
                ifspec=ifspec, if_index=if_index, if_tail=if_tail, hop=hop,
                **common)


async def scheduler(hosts: list[Host], interval: float, stagger: float,
                    state: dict) -> None:
    """Vystřeluje pingy na společné mřížce řádků.

    Mřížka běží na nejmenším intervalu ze všech hostů (per-host i=, jinak
    globální -i); hosty s delším intervalem pingují jen v některých řádcích
    a mezilehlé buňky nechávají prázdné. `stagger` posune odeslání pingů
    jednotlivých hostů o násobek offsetu, aby neodešly naráz."""
    base = min([interval] + [h.interval for h in hosts
                             if h.interval is not None])
    loop = asyncio.get_running_loop()
    due = {h: 0.0 for h in hosts}          # 0 = hned při prvním ticku
    seq = 0
    while not state["quit"]:
        seq += 1
        state["seq"] = seq
        now = loop.time()
        k = 0
        for h in hosts:
            if now >= due[h] - base * 0.5:     # tolerance zaokrouhlení mřížky
                asyncio.create_task(one_ping(h, seq, state, delay=k * stagger))
                due[h] = now + (h.interval if h.interval is not None
                                else interval)
                k += 1
        if state.get("dirty"):
            state["dirty"].set()
        await asyncio.sleep(base)


# ── remote: skupina cílů běží přes `<transport> pingtui --json …` ─────────────

def _apply_remote_event(obj: dict, by_rspec: dict, offset: int,
                        state: dict) -> None:
    """Promítne JSON událost z remote instance do lokálního Host sloupce."""
    host = by_rspec.get(obj.get("host"))
    event = obj.get("event")
    if host is None or not isinstance(obj.get("seq"), int):
        return
    seq = obj["seq"] + offset
    if event == "note":
        _set_note(state, host, seq, str(obj.get("kind", "resolve")),
                  str(obj.get("text", "")))
        return
    if event == "send":
        if seq not in host.pings:
            p = Ping(seq, PENDING, created=time.monotonic(), wall=time.time())
            host.add(p)
            _notify(state, "send", host, p)
    elif event == "result":
        p = host.pings.get(seq)
        if p is None:
            p = Ping(seq, PENDING, created=time.monotonic(), wall=time.time())
            host.add(p)
        if p.status != PENDING:
            return                                   # duplicitní výsledek
        p.status = obj.get("status", ERROR)
        p.rtt = obj.get("rtt")
        p.msg = obj.get("msg", "")
        p.detail = obj.get("detail", "")
        p.ttl = obj.get("ttl")
        host.resolve(p)
        _notify(state, "result", host, p)


def _feeder_error(group: list, transport: str, why: str, state: dict) -> None:
    """Zapíše chybu spojení jako řádek do všech sloupců skupiny."""
    for h in group:
        p = Ping(h.last_ping + 1, ERROR, msg="spojení selhalo",
                 detail=f"[{transport}] {why}"[:200], created=time.monotonic(),
                 wall=time.time())
        h.add(p)
        h.resolve(p)
        _notify(state, "result", h, p)


async def remote_feeder(transport: str, group: list, args, state: dict) -> None:
    """Udržuje jedno remote spojení pro celou skupinu cílů se stejným
    transportem: spustí `<transport> <remote-cmd> --json <cíle…>`, čte JSON
    události a plní z nich lokální sloupce. Při pádu se s odstupem restartuje."""
    backoff = 2.0
    while not state["quit"]:
        # @@ hosté: dej lokálnímu překladu (hlavní proces, mimo namespace)
        # krátkou šanci doběhnout, ať je stihneme do prvního spojení. Čekáme
        # souběžně a jen na ty, u kterých překlad ještě neselhal — cíl bez
        # řešení (např. _gateway bez routy) nesmí blokovat ostatní; přidá se
        # pak sám přes restart, až (pokud) se vůbec přeloží.
        waiting = [h for h in group if h.local_resolve
                   and h.prober.ip is None and not h.prober.fail]
        if waiting:
            await asyncio.wait(
                [asyncio.create_task(h.prober.ready.wait()) for h in waiting],
                timeout=3.0)
        # co za specifikaci pošleme remote: @@ → přeložená IP (+ per-host
        # parametry, aby platily i tam), jinak beze změny
        sent_ip = {h: h.prober.ip for h in group if h.local_resolve}
        sent = {h: ((sent_ip[h] + h.params_str) if h.local_resolve
                    else h.remote_spec)
                for h in group if not h.local_resolve or sent_ip[h] is not None}
        active = list(sent)
        # @@ cíle, které se ještě nepřeložily → zatím je neposíláme, ale hlídáme
        # je: až se přeloží, spojení restartujeme, aby se do něj přidaly
        pending_at = [h for h in group if h.local_resolve and h.prober.ip is None]
        if not active:
            # lokální překlad ještě nedoběhl → nic neodesíláme a nevkládáme
            # falešné chybové pingy; důvod je vidět v note řádku z resolveru
            await asyncio.sleep(2.0)
            continue
        by_rspec = {sent[h]: h for h in active}

        # offset zarovná seq remote pingů na aktuální pozici mřížky, aby dorazily
        # na živý konec tabulky (a ne do minulosti). Maximum z pozice mřížky
        # (state["seq"], řízené lokálními hosty) a z posledních skutečných pingů
        # skupiny: po restartu seq plynule navazuje a při zpožděném startu
        # (čekání na @@ překlad, výpadek spojení) se remote skupina nezobrazí
        # posunutá o desítky ticků dozadu. Noty ho neposouvají (jen last_ping).
        offset = max([state.get("seq", 0)] + [h.last_ping for h in group])
        cmd = (shlex.split(transport) + shlex.split(args.remote_cmd)
               + ["--json", "-i", str(args.interval), "-t", str(args.timeout),
                  "-w", str(args.max_wait), "-s", str(args.stagger),
                  "-r", str(args.resolve_interval)]
               + [sent[h] for h in active])
        stderr_tail: list[str] = []
        proc = None
        restart = False                              # změna @@ překladu → restart
        gen0 = state.get("rgen", 0)                  # klávesa 'r' → restart
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)

            async def _drain_stderr():
                while line := await proc.stderr.readline():
                    txt = line.decode(errors="replace").strip()
                    if txt:
                        stderr_tail.append(txt)
                        del stderr_tail[:-3]
            drain = asyncio.create_task(_drain_stderr())

            while line := await proc.stdout.readline():
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue                        # MOTD/banner na stdout
                if obj.get("event") in ("send", "result", "note"):
                    _apply_remote_event(obj, by_rspec, offset, state)
                    backoff = 2.0                   # spojení žije
                # lokální překlad @@ cíle se změnil, nebo uživatel vynutil
                # nový překlad (klávesa 'r') → restart s čerstvým překladem
                if (state.get("rgen", 0) != gen0
                        or any(h.local_resolve and h.prober.ip != sent_ip[h]
                               for h in active)
                        or any(h.prober.ip is not None for h in pending_at)):
                    restart = True
                    proc.terminate()
                    break
            if not restart:
                await proc.wait()
            drain.cancel()
        except asyncio.CancelledError:
            raise
        except OSError as e:
            stderr_tail.append(str(e))
        finally:
            if proc and proc.returncode is None:
                proc.terminate()
        if state["quit"]:
            return
        if restart:
            continue                                 # záměrný restart: bez chyb
        why = stderr_tail[-1] if stderr_tail else f"exit {proc.returncode if proc else '?'}"
        _feeder_error(group, transport, why, state)
        await asyncio.sleep(backoff)
        backoff = min(backoff * 2, 30.0)


async def engine(hosts: list[Host], args, state: dict) -> None:
    """Spustí lokální scheduler + jeden feeder na každý unikátní transport."""
    local = [h for h in hosts if not h.transport]
    groups: dict[str, list[Host]] = {}
    for h in hosts:
        if h.transport:
            groups.setdefault(h.transport, []).append(h)
    tasks = []
    if local:
        tasks.append(asyncio.create_task(
            scheduler(local, args.interval, args.stagger, state)))
    # periodický resolve ICMP cílů (+ note řádky s IP/reverse); patří sem
    # i @@ hosté (jméno překládá hlavní proces, ping běží remote) a IP
    # literály (u těch běží aspoň reverzní překlad)
    for h in hosts:
        if isinstance(h.prober, IcmpProbe):
            r = (h.resolve_int if h.resolve_int is not None
                 else args.resolve_interval)
            tasks.append(asyncio.create_task(
                resolver_task(h, h.prober, r, state)))
    for transport, group in groups.items():
        tasks.append(asyncio.create_task(
            remote_feeder(transport, group, args, state)))
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.cancel()


# ── vykreslování ──────────────────────────────────────────────────────────────

SEQW = 7          # šířka prvního sloupce (číslo pingu / název metriky)
TIMEW = 9         # šířka sloupce s časem odeslání packetu (HH:MM:SS)
TIMEOUT_X = 1.0   # práh X: po tolika s bez odpovědi = timeout (a ztráta)
MAX_WAIT = 10.0   # jak dlouho ping ještě běží a čeká na pozdní odpověď

# Prahy pro odstupňované barvení (zelená → žlutá → červená)
LAT_OK = 100.0    # ms: pod tím zelená
LAT_WARN = 300.0  # ms: pod tím žlutá, nad červená
LOSS_WARN = 20.0  # %: nenulová ztráta pod tím žlutá, nad červená

# barevné páry: 1 zelená, 2 červená, 3 žlutá, 4 tyrkysová (note řádky)
GREEN, RED, YELLOW, CYAN = 1, 2, 3, 4


def lat_color(ms: float | None) -> int:
    """Barva podle prodlevy: <100 ms zelená, <300 ms žlutá, jinak červená."""
    if ms is None:
        return 0
    if ms < LAT_OK:
        return GREEN
    if ms < LAT_WARN:
        return YELLOW
    return RED


def loss_color(pct: float) -> int:
    """Barva podle ztráty: 0 % zelená, malá ztráta žlutá, velká červená."""
    if pct <= 0:
        return GREEN
    return YELLOW if pct < LOSS_WARN else RED


def _ms(v: float | None) -> str:
    return f"{v:.1f}ms" if v is not None else "—"


def _fmt_ttl(ttl: int) -> str:
    """Kompaktní TTL: 45s / 12m / 3h."""
    if ttl >= 3600:
        return f"{ttl // 3600}h"
    if ttl >= 60:
        return f"{ttl // 60}m"
    return f"{ttl}s"


# Metriky do spodních řádků tabulky: (název, text(host), barva(host)).
# Vše O(1) z inkrementálních statistik Host — žádné procházení historie.
METRICS = [
    ("odesláno", lambda h: str(h.sent), lambda h: 0),
    ("přijato",  lambda h: str(h.recv), lambda h: GREEN),
    ("ztráta",   lambda h: f"{h.loss:.0f}%", lambda h: loss_color(h.loss)),
    ("min",      lambda h: _ms(h.rtt_min), lambda h: lat_color(h.rtt_min)),
    ("ø",        lambda h: _ms(h.avg), lambda h: lat_color(h.avg)),
    ("max",      lambda h: _ms(h.rtt_max), lambda h: lat_color(h.rtt_max)),
]


def _kind_order(kind: str) -> int:
    """Pořadí note řádků v rámci ticku: → překlad, ← reverz, pak chyby."""
    return {"resolve": 0, "reverse": 1}.get(kind, 2)


def _tick_wall(hosts: list[Host], seq: int) -> float | None:
    """Nejstarší wall-clock čas odeslání packetu v daném ticku (nebo None,
    když v tomto ticku žádný host nepingoval — jen noty)."""
    best = None
    for h in hosts:
        p = h.pings.get(seq)
        if p and p.wall and (best is None or p.wall < best):
            best = p.wall
    return best


def _hhmmss(wall: float | None) -> str:
    """Wall-clock čas jako HH:MM:SS (prázdné, když čas není)."""
    return time.strftime("%H:%M:%S", time.localtime(wall)) if wall else ""


def _date_label(wall: float | None, now_wall: float) -> str:
    """Kompaktní datum `wall`, pokud nespadá do dneška (jinak ''). Vejde se do
    TIMEW: 'MM-DD' ve stejném roce, jinak 'YY-MM-DD'."""
    if not wall:
        return ""
    lt = time.localtime(wall)
    tt = time.localtime(now_wall)
    if (lt.tm_year, lt.tm_mon, lt.tm_mday) == (tt.tm_year, tt.tm_mon, tt.tm_mday):
        return ""
    if lt.tm_year != tt.tm_year:
        return time.strftime("%y-%m-%d", lt)
    return time.strftime("%m-%d", lt)


def cell_text(p: Ping | None, colw: int, now: float,
              tx: float | None = None) -> tuple[str, int]:
    """Vrátí (text, barva) pro buňku.

    Barva 3 (žlutá) = odpověď ještě nedorazila: platí pro pending i timeout,
    protože pozdní odpověď ještě může dorazit. Pending starší než práh `tx`
    (per-host t=, jinak globální -t; stejný práh jako u výpočtu úspěšnosti)
    se zobrazí jako timeout; když reálná odpověď dorazí i po timeoutu,
    buňka se překreslí na skutečný stav.
    """
    if p is None:
        return "", 0
    if p.status == OK:
        if p.ttl is not None:      # DNS: doba resolve + platnost odpovědi
            return f"{p.rtt:.0f}ms/{_fmt_ttl(p.ttl)}", lat_color(p.rtt)
        return f"{p.rtt:.1f}ms", lat_color(p.rtt)
    if p.status == ERROR:
        return (p.msg or "ERR")[:colw - 1], RED
    if p.status == TIMEOUT:
        return "- - -".center(colw), YELLOW
    # PENDING: po uplynutí prahu ho vizuálně označíme za timeout (žlutě)
    if now - p.created >= (tx if tx is not None else TIMEOUT_X):
        return "- - -".center(colw), YELLOW
    return "· · ·".center(colw), YELLOW


def _put(scr, y: int, x: int, text: str, n: int, attr: int = 0) -> None:
    """Bezpečný zápis: ořízne na obrazovku a spolkne chyby curses (zápis do
    pravého dolního rohu apod.) — tabulka širší než terminál se jen ořízne."""
    h, w = scr.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    n = min(n, w - x)
    if n <= 0:
        return
    try:
        scr.addnstr(y, x, text, n, attr)
    except curses.error:
        pass


def draw(stdscr, hosts: list[Host], state: dict, start_ts: float) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    # výška tabulky: lokální ticky i ticky došlé z remote sloupců
    max_seq = max([state.get("seq", 0)] + [hh.last_seq for hh in hosts])
    now = time.monotonic()

    # Přirozená šířka sloupce podle obsahu (název hosta / note text / rtt),
    # NEroztahujeme na celou šířku terminálu — vpravo zůstane mezera.
    # Pokud se to nevejde, sloupce zúžíme, aby se vešly.
    content = max(max(len(h.label), h.note_w) for h in hosts) + 1
    natural = max(9, min(28, content))
    fit = (w - SEQW - TIMEW - 1) // len(hosts)
    colw = max(9, min(natural, fit))
    table_w = min(w, SEQW + TIMEW + colw * len(hosts))
    cw = colw - 1                    # užitná šířka buňky

    # hlavička: labely delší než buňka se lámou na dva řádky; pod jmény
    # navíc aktuální stav překladu (→) a reverzu (←), pokud už nějaký je
    hdr_rows = 2 if any(len(hh.label) > cw for hh in hosts) else 1
    hdr_res = any(hh.last_resolve for hh in hosts)
    hdr_rev = any(hh.last_reverse for hh in hosts)
    data_top = 2 + hdr_rows + int(hdr_res) + int(hdr_rev)

    # svislé rozvržení (odspodu): nápověda, řádky metrik, oddělovač, tabulka.
    sep_y = h - 2 - len(METRICS)     # řádek s oddělovačem statistik
    nrows = max(1, sep_y - data_top)  # kolik řádků tabulky se vejde

    # Řádky tabulky: každý tick = jeden zarovnaný řádek, a hned pod ním
    # případné plnošířkové řádky s detailem negativní odpovědi. Sbíráme jen
    # potřebné okno odspodu (od nejnovějšího) — O(viditelné řádky), ne O(historie).
    # Note řádky delší než buňka se lámou na dva; jejich přesný počet drží
    # histogram délek (nlh), takže total zůstává O(1).
    noterows = state.get("noterows", {})
    nlh = state.get("nlh", {})
    wrap_extra = sum(c for length, c in nlh.items() if length > cw)
    total = (max_seq + sum(host.neg for host in hosts)
             + state.get("nnoterows", 0) + wrap_extra)

    # Kotvení scrollu: scroll_off je vzdálenost od živého konce. Když je
    # uživatel odscrollovaný (off > 0), nové řádky dole nesmí obsahem hýbat —
    # off proto zvětšíme o přírůstek řádků, takže okno zůstane na místě.
    scroll_off = state.get("scroll_off", 0)
    prev_total = state.get("prev_total", total)
    if scroll_off > 0 and total > prev_total:
        scroll_off += total - prev_total
    scroll_off = min(scroll_off, max(0, total - nrows))
    state["prev_total"] = total
    state["scroll_off"] = scroll_off
    state["nrows"] = nrows
    state["total_rows"] = total

    need = scroll_off + nrows
    rows_bottom_up: list = []          # index 0 = úplně spodní řádek
    seq = max_seq
    while seq >= 1 and len(rows_bottom_up) < need:
        # v pořadí top→bottom: resolve/reverse NAD tickem (proběhly před ním),
        # detaily chyb POD tickem (jsou výsledkem toho pingu)
        block = []
        for kind, maxlen in sorted(noterows.get(seq, {}).items(),
                                   key=lambda kv: _kind_order(kv[0])):
            block.append(("noterow", seq, kind, 0))
            if not kind.startswith("err:") and maxlen > cw:
                block.append(("noterow", seq, kind, 1))   # pokračovací řádek
        block.append(("tick", seq))
        for host in hosts:
            p = host.pings.get(seq)
            if p and p.detail:
                block.append(("detail", seq, host.label, p.detail))
        for r in reversed(block):
            rows_bottom_up.append(r)
        seq -= 1
    visible = list(reversed(rows_bottom_up[scroll_off:scroll_off + nrows]))

    # datum prvního (nejhořejšího) zobrazeného řádku — do hlavičky sloupce
    # s časem, ale jen když nejstarší viditelný tick nespadá do dneška
    first_wall = next((wt for it in visible
                       if (wt := _tick_wall(hosts, it[1]))), None)
    hdr_date = _date_label(first_wall, time.time())

    # titulek
    title = (f" TUI ping — {len(hosts)} adres · interval {state['interval']}s"
             f" · timeout {state['timeout']}s · {state.get('method', '')} ")
    _put(stdscr, 0, 0, title.ljust(w), w, curses.A_BOLD | curses.A_REVERSE)

    # hlavička s adresami (dlouhé labely na dva řádky; podtržený je spodní
    # řádek hlavičky) + aktuální stav překladu a reverzu pod jmény
    for row in range(hdr_rows):
        y = 2 + row
        name_last = row == hdr_rows - 1
        attr = curses.A_BOLD | (0 if hdr_res or hdr_rev or not name_last
                                else curses.A_UNDERLINE)
        _put(stdscr, y, 0, ("ping" if name_last else "").rjust(SEQW), SEQW,
             attr)
        x = SEQW + TIMEW
        for host in hosts:
            part = host.label[row * cw:(row + 1) * cw]
            _put(stdscr, y, x, part.rjust(colw), colw, attr)
            x += colw
    if hdr_date:                       # datum do hlavičky sloupce s časem
        yd = 2 + hdr_rows - 1
        dattr = curses.A_BOLD | (0 if hdr_res or hdr_rev else curses.A_UNDERLINE)
        _put(stdscr, yd, SEQW, hdr_date.rjust(TIMEW), TIMEW, dattr)
    y = 2 + hdr_rows
    for kind_attr, show in (("last_resolve", hdr_res), ("last_reverse", hdr_rev)):
        if not show:
            continue
        last = y == data_top - 1
        base = curses.color_pair(CYAN) | (curses.A_UNDERLINE if last else 0)
        sym = "→" if kind_attr == "last_resolve" else "←"
        _put(stdscr, y, 0, sym.rjust(SEQW), SEQW, base | curses.A_BOLD)
        x = SEQW + TIMEW
        for host in hosts:
            val = getattr(host, kind_attr)[:cw]
            _put(stdscr, y, x, val.rjust(colw), colw, base)
            x += colw
        y += 1

    # datové řádky, nejnovější dole
    for i, item in enumerate(visible):
        y = data_top + i
        if y >= sep_y:
            break
        if item[0] == "tick":
            seq = item[1]
            _put(stdscr, y, 0, f"#{seq}".rjust(SEQW), SEQW, curses.A_DIM)
            _put(stdscr, y, SEQW, _hhmmss(_tick_wall(hosts, seq)).rjust(TIMEW),
                 TIMEW, curses.A_DIM)
            x = SEQW + TIMEW
            for host in hosts:
                txt, color = cell_text(host.pings.get(seq), colw, now, host.tx)
                attr = curses.color_pair(color) if color else 0
                if txt:
                    _put(stdscr, y, x, txt.rjust(colw), colw, attr)
                x += colw
        elif item[0] == "detail":  # plnošířkový řádek s detailem negativní odpovědi
            _, seq, label, detail = item
            line = f"  ⚠ #{seq} {label}: {detail}"
            _put(stdscr, y, 0, line[:w - 1].ljust(w - 1), w - 1,
                 curses.color_pair(RED))
        elif item[0] == "noterow" and item[2].startswith("err:"):
            # chyba překladu: přes celý řádek, stejně jako zamítavá odpověď
            _, seq, kind, _part = item
            host = next((hh for hh in hosts if hh.spec == kind[4:]), None)
            n = next((nn for nn in host.notes.get(seq, ())
                      if nn.kind == kind), None) if host else None
            if host and n:
                line = f"  ⚠ #{seq} {host.label}: {n.text}"
                _put(stdscr, y, 0, line[:w - 1].ljust(w - 1), w - 1,
                     curses.color_pair(RED))
        else:  # "noterow": resolve/reverse zarovnané do sloupců cílů;
            # část 1 = pokračování textů zalomených na druhý řádek
            _, seq, kind, part = item
            sym = ("→" if kind == "resolve" else "←") if part == 0 else ""
            _put(stdscr, y, 0, sym.rjust(SEQW), SEQW,
                 curses.color_pair(CYAN) | curses.A_BOLD)
            x = SEQW + TIMEW
            for host in hosts:
                n = next((nn for nn in host.notes.get(seq, ())
                          if nn.kind == kind), None)
                if n:
                    chunk = n.text[part * cw:(part + 1) * cw]
                    if chunk:
                        _put(stdscr, y, x, chunk.rjust(colw), colw,
                             curses.color_pair(CYAN))
                x += colw

    # ── oddělovač + řádky metrik (zarovnané do stejných sloupců jako pingy) ──
    if sep_y >= data_top:
        _put(stdscr, sep_y, 0, "─" * table_w, table_w, curses.A_DIM)
        for j, (label, fn, colorfn) in enumerate(METRICS):
            y = sep_y + 1 + j
            if y >= h - 1:
                break
            _put(stdscr, y, 0, label.rjust(SEQW), SEQW,
                 curses.A_BOLD | curses.A_DIM)
            x = SEQW + TIMEW
            for host in hosts:
                _put(stdscr, y, x, fn(host).rjust(colw), colw,
                     curses.color_pair(colorfn(host)))
                x += colw

    # nápověda na posledním řádku
    elapsed = time.monotonic() - start_ts
    live = "živě" if scroll_off == 0 else f"↑{scroll_off}"
    hint = (f"[{elapsed:.0f}s]  q=konec  r=přeložit znovu  ↑/↓=scroll  "
            f"home/end=okraje  [{live}]")
    _put(stdscr, h - 1, 0, hint.ljust(w - 1), w - 1, curses.A_DIM)
    stdscr.noutrefresh()
    curses.doupdate()


async def renderer(stdscr, hosts, state, start_ts) -> None:
    # Klávesy budí renderer okamžitě přes reader na stdin — díky tomu může být
    # záložní tik dlouhý a v klidu nesmyslně nežere CPU.
    loop = asyncio.get_running_loop()
    try:
        loop.add_reader(0, state["dirty"].set)
        have_reader = True
    except (OSError, ValueError):
        have_reader = False

    try:
        while not state["quit"]:
            draw(stdscr, hosts, state, start_ts)
            # zpracování kláves
            while True:
                ch = stdscr.getch()
                if ch == -1:
                    break
                _handle_key(ch, state)
            # Překreslení řízené událostí: probudíme se ihned, jakmile se něco
            # změní (odeslání pending / příchod odpovědi / stisk klávesy).
            # Když nic „nedozrává", spíme dlouho → v klidu skoro nulové CPU.
            active = any(h.inflight for h in hosts)
            timeout = 0.25 if active else 1.0
            if not have_reader:
                timeout = min(timeout, 0.1)   # bez readeru musíme pollovat klávesy
            try:
                await asyncio.wait_for(state["dirty"].wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass
            state["dirty"].clear()
    finally:
        if have_reader:
            loop.remove_reader(0)


def _handle_key(ch: int, state: dict) -> None:
    total = state.get("total_rows", 1)
    nrows = state.get("nrows", 1)
    max_off = max(0, total - nrows)
    off = state.get("scroll_off", 0)
    if ch in (ord("q"), 27):
        state["quit"] = True
    elif ch == curses.KEY_UP:
        state["scroll_off"] = min(max_off, off + 1)
    elif ch == curses.KEY_DOWN:
        state["scroll_off"] = max(0, off - 1)
    elif ch == curses.KEY_PPAGE:
        state["scroll_off"] = min(max_off, off + nrows)
    elif ch == curses.KEY_NPAGE:
        state["scroll_off"] = max(0, off - nrows)
    elif ch == curses.KEY_HOME:
        state["scroll_off"] = max_off
    elif ch == curses.KEY_END:
        state["scroll_off"] = 0
    elif ch == ord("r"):
        # vynutit okamžitý nový překlad všech cílů (vč. restartu remote
        # spojení, aby se přeložilo i na vzdálené straně)
        state["rgen"] = state.get("rgen", 0) + 1
        ev = state.get("reresolve")
        if ev:
            ev.set()
            ev.clear()


# ── zapojení do curses ────────────────────────────────────────────────────────

async def amain(stdscr, hosts, args) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)    # ok
    curses.init_pair(2, curses.COLOR_RED, -1)      # chyba
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # pending / timeout
    curses.init_pair(4, curses.COLOR_CYAN, -1)     # note (resolve/reverse)

    # vyber pinger (nativní ICMP socket, nebo subprocess fallback)
    global PINGER
    PINGER = build_pinger(args.subprocess, args.cmd)
    _assign_probers(hosts)
    state = {
        "quit": False, "seq": 0, "scroll_off": 0, "dirty": asyncio.Event(),
        "reresolve": asyncio.Event(), "rgen": 0,
        "interval": args.interval, "timeout": TIMEOUT_X,
        "method": "subprocess" if isinstance(PINGER, SubprocessPinger) else "nativní",
    }
    start_ts = time.monotonic()
    eng = asyncio.create_task(engine(hosts, args, state))
    try:
        await renderer(stdscr, hosts, state, start_ts)
    finally:
        state["quit"] = True
        eng.cancel()
        await asyncio.gather(eng, return_exceptions=True)
        if isinstance(PINGER, NativePinger):
            PINGER.close()


def _assign_probers(hosts: list[Host]) -> None:
    """Lokálním cílům bez sondy přiřadí ICMP sondu (DNS už mají z parse_spec).
    Hosté s @@ (local_resolve) dostanou sondu taky — nepinguje, slouží jen
    jako držák lokálního překladu (ip/ready) pro feeder."""
    for h in hosts:
        if (not h.transport or h.local_resolve) and h.prober is None:
            h.prober = IcmpProbe(h.addr, h.family, force_resolve=bool(h.hop))


def run(stdscr, hosts, args) -> None:
    try:
        asyncio.run(amain(stdscr, hosts, args))
    except KeyboardInterrupt:
        pass


# ── režim --json: místo TUI vypisuje na stdout JSON událost za každou akci ─────

def _emit(obj: dict) -> None:
    """Vypíše jednu JSON událost (JSON Lines) a hned flushne."""
    try:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    except BrokenPipeError:
        raise KeyboardInterrupt   # příjemce zavřel rouru → skonči


async def amain_json(hosts, args) -> None:
    global PINGER
    PINGER = build_pinger(args.subprocess, args.cmd)
    _assign_probers(hosts)
    _emit({"event": "start", "t": time.time(),
           "hosts": [h.spec for h in hosts],
           "interval": args.interval, "timeout": TIMEOUT_X,
           "max_wait": MAX_WAIT, "stagger": args.stagger,
           "method": "subprocess" if isinstance(PINGER, SubprocessPinger)
                     else "native"})
    # bez dirty (žádné překreslování); jen emit událostí přes _notify
    state = {"quit": False, "seq": 0, "emit": _emit, "dirty": None,
             "reresolve": asyncio.Event(), "rgen": 0,
             "interval": args.interval}
    try:
        await engine(hosts, args, state)
    finally:
        if isinstance(PINGER, NativePinger):
            PINGER.close()


def run_json(hosts, args) -> None:
    try:
        asyncio.run(amain_json(hosts, args))
    except KeyboardInterrupt:
        pass


def print_history(hosts: list[Host]) -> None:
    """Po ukončení TUI vypíše kompletní barevnou historii pingů do terminálu.

    curses používá alternativní obrazovku, která se při ukončení smaže — proto
    zrenderujeme finální tabulku znovu jako obyčejný text s ANSI barvami, aby
    zůstala trvale v historii terminálu. Barvy odpovídají TUI; při přesměrování
    výstupu mimo terminál se vypíše bez barev.
    """
    import sys

    max_seq = max((max(h.pings, default=0) for h in hosts), default=0)
    if max_seq == 0:
        return
    colw = max(9, min(28, max(max(len(h.label), h.note_w) for h in hosts) + 1))
    color = sys.stdout.isatty()

    now = time.monotonic()
    R, B, DIM = "\x1b[0m", "\x1b[1m", "\x1b[2m"
    YEL, GRN, RED, CYN = "\x1b[33m", "\x1b[32m", "\x1b[31m", "\x1b[36m"
    # mapování barevného páru (viz lat_color/loss_color) na ANSI kód
    ANSI = {0: "", GREEN: GRN, YELLOW: YEL, 2: RED}

    def cell(p: Ping | None, tx: float) -> str:
        if p is None:
            return "-".rjust(colw)
        if p.status == OK:
            txt = (f"{p.rtt:.0f}ms/{_fmt_ttl(p.ttl)}" if p.ttl is not None
                   else f"{p.rtt:.1f}ms")
            txt, col = txt.rjust(colw), ANSI[lat_color(p.rtt)]
        elif p.status == ERROR:
            txt, col = (p.msg or "ERR")[:colw - 1].rjust(colw), RED
        elif p.status == TIMEOUT or now - p.created >= tx:
            txt, col = "- - -".center(colw), YEL   # timeout: žlutě jako nedoručeno
        else:
            txt, col = "· · ·".center(colw), YEL
        return f"{col}{txt}{R}" if color else txt

    def c(s: str, code: str) -> str:
        return f"{code}{s}{R}" if color else s

    print()
    cw = colw - 1
    print(c("Historie pingů:", B))
    # hlavička: dlouhé labely na dva řádky
    hdr_rows = 2 if any(len(h.label) > cw for h in hosts) else 1
    hdr_w = 7 + colw * len(hosts)
    for row_i in range(hdr_rows):
        last = row_i == hdr_rows - 1
        line = ("ping" if last else "").rjust(7)
        for h in hosts:
            line += h.label[row_i * cw:(row_i + 1) * cw].rjust(colw)
        print(c(line, B))
    # aktuální stav překladu a reverzu pod jmény
    for attr_name, sym in (("last_resolve", "→"), ("last_reverse", "←")):
        if any(getattr(h, attr_name) for h in hosts):
            line = c(sym.rjust(7), CYN)
            for h in hosts:
                line += c(getattr(h, attr_name)[:cw].rjust(colw), CYN)
            print(line)
    print(c("─" * hdr_w, DIM))
    for seq in range(1, max_seq + 1):
        # resolve/reverse řádky NAD tickem (proběhly před ním), do sloupců
        kinds: list[str] = []
        for host in hosts:
            for n in host.notes.get(seq, ()):
                if n.kind not in kinds:
                    kinds.append(n.kind)
        for kind in sorted(kinds, key=_kind_order):
            if kind.startswith("err:"):        # chyba překladu na celý řádek
                host = next((hh for hh in hosts if hh.spec == kind[4:]), None)
                n = next((nn for nn in host.notes.get(seq, ())
                          if nn.kind == kind), None) if host else None
                if host and n:
                    print(c(f"  ⚠ #{seq} {host.label}: {n.text}", RED))
                continue
            cells = [next((nn.text for nn in host.notes.get(seq, ())
                           if nn.kind == kind), "") for host in hosts]
            parts = 2 if any(len(t) > cw for t in cells) else 1
            for part in range(parts):          # dlouhé texty na dva řádky
                sym = ("→" if kind == "resolve" else "←") if part == 0 else ""
                row = c(sym.rjust(7), CYN)
                for t in cells:
                    row += c(t[part * cw:(part + 1) * cw].rjust(colw), CYN)
                print(row)
        row = c(f"#{seq}".rjust(7), DIM)
        for host in hosts:
            row += cell(host.pings.get(seq), host.tx)
        print(row)
        # plné detaily negativních odpovědí (unreachable, DNS, …) inline pod tickem
        for host in hosts:
            p = host.pings.get(seq)
            if p and p.detail:
                print(c(f"  ⚠ #{seq} {host.label}: {p.detail}", RED))
    print(c("─" * hdr_w, DIM))
    # metriky ve stejných sloupcích jako pingy, řádek na metriku
    for label, fn, colorfn in METRICS:
        row = c(label.rjust(7), B + DIM)
        for host in hosts:
            val = fn(host).rjust(colw)
            code = ANSI.get(colorfn(host), "")
            if color and code:
                val = f"{code}{val}{R}"
            row += val
        print(row)


TARGET_HELP = """\
Specifikace cíle (dělí se vždy prvním @ zleva):
  adresa                     lokální ICMP ping (IPv4 / IPv6 / jméno)
  v4:jméno / v6:jméno        vynutí IPv4/IPv6 překlad jména (default: dle systému)
  cíl^N                      pingat N-tý hop cesty k cíli (jako traceroute);
                             hop se dohledává periodicky jako překlad
  _gateway                   ping na default gateway (z routovací tabulky)
  gateway:<iface>            default gateway ("via") skrz daný interface
  if:<iface>[#n]             n-tá (default první) IP adresa interface
  if4:<iface>[#n]:<konec>    síťový prefix n-té IPv4 adresy interface
                             + doplněný konec (např. if4:eth0:21)
  if6:<iface>[#n]:<konec>    totéž pro IPv6 (např. if6:wg0:10:1)
  dns:jméno                  test DNS resolve přes systémový resolver
  dns:jméno@server[:port]    test DNS proti konkrétnímu serveru
  adresa@<příkaz>            remote: spustí `<příkaz> pingtui --json adresa`
  adresa@@<příkaz>           jméno přeloží hlavní proces (mimo namespace),
                             remote pinguje už hotovou IP; při změně překladu
                             se remote restartuje s novou IP
  dns:jméno@server@<příkaz>  DNS test proti serveru, spuštěný remote

  Stejný @<příkaz> u více cílů = jedno sdílené spojení.

Per-host parametry (čárkami hned za cílem, před prvním @):
  cíl,i=0.2,t=2,w=5,r=30,label=doma
    i / interval           frekvence pingu
    t / timeout            práh timeoutu (a započítání do ztráty)
    w / max-wait           max čekání na pozdní odpověď
    r / resolve-interval   frekvence resolve/reverse (0 = jen ručně klávesou 'r')
    label                  název sloupce v tabulce
  Řádky tabulky běží na nejmenším intervalu ze všech hostů; pomalejší hosty
  nechávají mezilehlé buňky prázdné.

DNS wildcards ve jméně dotazu (expandují se per dotaz):
  %i     sekvenční číslo dotazu
  %5h    5 znaků hashe seq (deterministické; N volitelné)
  %5r    5 náhodných znaků (N volitelné, výchozí 5)
  %5c    5 znaků náhodného identifikátoru session (stejný po celý běh)
  %%     literál %
  Např. dns:%5r.example.com obchází DNS cache.

Příklady:
  pingtui.py 8.8.8.8 1.1.1.1 example.com
  pingtui.py -i 2 -t 3 8.8.8.8 seznam.cz
  pingtui.py dns:google.com 'dns:seznam.cz@10.0.0.1:53'
  pingtui.py '8.8.8.8@ssh gw' 'dns:google.com@1.1.1.1@ssh gw'
  pingtui.py '8.8.8.8,label=direct@@net_direct'

Ovládání TUI:
  q / Esc      konec
  r            přeložit znovu (vč. restartu remote spojení)
  šipky ↑/↓    posun po řádcích (jinak drží živý konec)
  PgUp/PgDn    posun po stránkách
  home/end     skok na okraje
"""


def main() -> None:
    ap = argparse.ArgumentParser(
        description="TUI ping na více adres najednou.",
        epilog=TARGET_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hosts", nargs="+", help="adresy k pingání")
    ap.add_argument("-i", "--interval", type=float, default=1.0,
                    help="perioda mezi pingy v sekundách (výchozí 1)")
    ap.add_argument("-t", "--timeout", type=float, default=1.0,
                    help="za jak dlouho bez odpovědi označit ping za timeout "
                         "(a započítat do ztráty); pozdní odpověď se stejně "
                         "překreslí (výchozí 1)")
    ap.add_argument("-w", "--max-wait", type=float, default=10.0,
                    help="jak dlouho ping ještě čeká na pozdní odpověď, než to "
                         "vzdá (výchozí 10)")
    ap.add_argument("-s", "--stagger", type=float, default=0.0,
                    help="offset mezi odesláním pingů na jednotlivé adresy "
                         "v rámci jednoho tiku (s), aby neodešly naráz "
                         "(výchozí 0)")
    ap.add_argument("-r", "--resolve-interval", type=float, default=0.0,
                    help="jak často (s) automaticky obnovovat překlady "
                         "(DNS/gateway/if*/hop); 0 = jen na startu a na "
                         "klávesu 'r' (výchozí 0); při selhání se dál "
                         "používá starý překlad")
    ap.add_argument("--subprocess", action="store_true",
                    help="nepoužívat nativní ICMP socket, ale spouštět externí "
                         "příkaz ping (fallback pro kompatibilitu)")
    ap.add_argument("--cmd", default=DEFAULT_CMD,
                    help="příkaz pro subprocess režim; {host} a {w} (timeout) "
                         f"se dosadí (výchozí: {DEFAULT_CMD!r})")
    ap.add_argument("--json", action="store_true",
                    help="nekreslit TUI; na stdout vypisovat JSON událost "
                         "(JSON Lines) za každou akci — vhodné pro remote ping")
    ap.add_argument("--remote-cmd", default="pingtui",
                    help="jak se jmenuje pingtui na remote straně "
                         "(výchozí: pingtui)")
    args = ap.parse_args()
    global TIMEOUT_X, MAX_WAIT
    TIMEOUT_X = args.timeout
    MAX_WAIT = max(args.max_wait, args.timeout)

    try:
        hosts = [parse_spec(s) for s in args.hosts]
    except ValueError as e:
        ap.error(str(e))
    if args.json:
        run_json(hosts, args)
        return
    curses.wrapper(run, hosts, args)
    print_history(hosts)      # po ukončení TUI zůstane historie v terminálu


if __name__ == "__main__":
    main()
