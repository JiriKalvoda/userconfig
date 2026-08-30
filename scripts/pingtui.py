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
    adresa@<příkaz>              remote: `<příkaz> pingtui --json adresa`
    dns:jméno                    test DNS resolve (systémový resolver)
    dns:jméno@server[:port]      test DNS proti konkrétnímu serveru
    dns:jméno@server@<příkaz>    totéž, spuštěné remote
    Stejný @<příkaz> u více cílů = jedno sdílené spojení.

Ovládání:
    q / Esc     konec
    šipky ↑/↓   posun po řádcích (jinak drží nejnovější)
    end         zpět na živý konec
"""

import argparse
import asyncio
import curses
import json
import os
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


@dataclass
class PingResult:
    """Výsledek jedné sondy (nezávislý na tom, kdo ji provedl)."""
    status: str
    rtt: float | None = None       # ms
    msg: str = ""
    detail: str = ""
    ttl: int | None = None         # u DNS: TTL odpovědi (s)


@dataclass
class Host:
    addr: str
    label: str = ""                # zobrazovaný název sloupce (default = addr)
    spec: str = ""                 # plná specifikace (JSON id; default = addr)
    remote_spec: str = ""          # specifikace předávaná remote instanci
    transport: str = ""            # neprázdné = remote (přes tento příkaz, např. "ssh h")
    prober: object = None          # lokální sonda (IcmpProbe/DnsProbe); remote: None
    pings: dict[int, Ping] = field(default_factory=dict)
    sent: int = 0
    recv: int = 0
    lost: int = 0                  # finálně ztracené (ERROR + TIMEOUT)
    neg: int = 0                   # počet pingů s detailem (pro počítání řádků)
    last_seq: int = 0              # nejvyšší seq (pro výšku tabulky)
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

    @property
    def avg(self) -> float | None:
        return self.rtt_sum / self.recv if self.recv else None

    @property
    def loss(self) -> float:
        """Ztráta v % jen z pingů, které už dorazily, nebo jsou na cestě
        déle než TIMEOUT_X s. Čerstvé pending (které ještě mají čas dorazit)
        se nezapočítávají, aby ztráta zbytečně neposkakovala. O(inflight)."""
        now = time.monotonic()
        old_pending = sum(1 for s in self.inflight
                          if (p := self.pings.get(s)) and now - p.created >= TIMEOUT_X)
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
    p = Ping(seq=seq, status=PENDING, created=time.monotonic())
    host.add(p)                    # okamžitě "pending" do tabulky
    _notify(state, "send", host, p)

    try:
        try:
            res = await host.prober.probe(MAX_WAIT)
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

class IcmpProbe:
    """Lokální ICMP sonda — deleguje na sdílený PINGER."""

    def __init__(self, addr: str):
        self.addr = addr

    async def probe(self, max_wait: float) -> PingResult:
        return await PINGER.ping(self.addr, max_wait)


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
    Používá vlastní UDP dotaz — server buď explicitní, nebo systémový."""

    def __init__(self, name: str, server: str | None = None, port: int = 53):
        self.name = name
        self.server = server
        self.port = port

    async def probe(self, max_wait: float) -> PingResult:
        loop = asyncio.get_running_loop()
        server = self.server or _default_dns()
        where = f"dns:{self.name}@{server}:{self.port}"
        _dns_qid[0] = qid = (_dns_qid[0] + 1) & 0xFFFF
        pkt = _build_dns_query(qid, self.name)
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
    head, sep, rest = spec.partition("@")
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
        if server:
            srv = f"[{server}]" if ":" in server else server   # IPv6 → závorky
            remote_spec = f"dns:{name}@{srv}:{port}"
        else:
            remote_spec = f"dns:{name}"
        return Host(addr=name, label=spec, spec=spec, remote_spec=remote_spec,
                    transport=transport,
                    prober=None if transport else DnsProbe(name, server, port))
    # obyčejný ping: vše za prvním @ je transport
    transport = rest if sep else ""
    return Host(addr=head, label=spec, spec=spec, remote_spec=head,
                transport=transport)


async def scheduler(hosts: list[Host], interval: float, stagger: float,
                    state: dict) -> None:
    """Každých `interval` sekund vystřelí ping na každou adresu.

    `stagger` posune odeslání pingů na jednotlivé adresy o násobek offsetu
    vůči sobě, aby neodešly všechny naráz (a netrigly rate-limit)."""
    seq = 0
    while not state["quit"]:
        seq += 1
        state["seq"] = seq
        for k, h in enumerate(hosts):
            asyncio.create_task(one_ping(h, seq, state, delay=k * stagger))
        if state.get("dirty"):
            state["dirty"].set()
        await asyncio.sleep(interval)


# ── remote: skupina cílů běží přes `<transport> pingtui --json …` ─────────────

def _apply_remote_event(obj: dict, by_rspec: dict, offset: int,
                        state: dict) -> None:
    """Promítne JSON událost z remote instance do lokálního Host sloupce."""
    host = by_rspec.get(obj.get("host"))
    event = obj.get("event")
    if host is None or not isinstance(obj.get("seq"), int):
        return
    seq = obj["seq"] + offset
    if event == "send":
        if seq not in host.pings:
            p = Ping(seq, PENDING, created=time.monotonic())
            host.add(p)
            _notify(state, "send", host, p)
    elif event == "result":
        p = host.pings.get(seq)
        if p is None:
            p = Ping(seq, PENDING, created=time.monotonic())
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
        p = Ping(h.last_seq + 1, ERROR, msg="spojení selhalo",
                 detail=f"[{transport}] {why}"[:200], created=time.monotonic())
        h.add(p)
        h.resolve(p)
        _notify(state, "result", h, p)


async def remote_feeder(transport: str, group: list, args, state: dict) -> None:
    """Udržuje jedno remote spojení pro celou skupinu cílů se stejným
    transportem: spustí `<transport> <remote-cmd> --json <cíle…>`, čte JSON
    události a plní z nich lokální sloupce. Při pádu se s odstupem restartuje."""
    by_rspec = {h.remote_spec: h for h in group}
    backoff = 2.0
    while not state["quit"]:
        offset = max(h.last_seq for h in group)      # ať seq po restartu navazují
        cmd = (shlex.split(transport) + shlex.split(args.remote_cmd)
               + ["--json", "-i", str(args.interval), "-t", str(args.timeout),
                  "-w", str(args.max_wait), "-s", str(args.stagger)]
               + [h.remote_spec for h in group])
        stderr_tail: list[str] = []
        proc = None
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
                if obj.get("event") in ("send", "result"):
                    _apply_remote_event(obj, by_rspec, offset, state)
                    backoff = 2.0                   # spojení žije
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
TIMEOUT_X = 1.0   # práh X: po tolika s bez odpovědi = timeout (a ztráta)
MAX_WAIT = 10.0   # jak dlouho ping ještě běží a čeká na pozdní odpověď

# Prahy pro odstupňované barvení (zelená → žlutá → červená)
LAT_OK = 100.0    # ms: pod tím zelená
LAT_WARN = 300.0  # ms: pod tím žlutá, nad červená
LOSS_WARN = 20.0  # %: nenulová ztráta pod tím žlutá, nad červená

# barevné páry: 1 zelená, 2 červená, 3 žlutá
GREEN, RED, YELLOW = 1, 2, 3


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


def cell_text(p: Ping | None, colw: int, now: float) -> tuple[str, int]:
    """Vrátí (text, barva) pro buňku.

    Barva 3 (žlutá) = odpověď ještě nedorazila: platí pro pending i timeout,
    protože pozdní odpověď ještě může dorazit. Pending starší než TIMEOUT_X
    se zobrazí jako timeout (stejný práh X jako u výpočtu úspěšnosti); když
    reálná odpověď dorazí i po timeoutu, buňka se překreslí na skutečný stav.
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
    # PENDING: po uplynutí X ho vizuálně označíme za timeout (žlutě)
    if now - p.created >= TIMEOUT_X:
        return "- - -".center(colw), YELLOW
    return "· · ·".center(colw), YELLOW


def draw(stdscr, hosts: list[Host], state: dict, start_ts: float) -> None:
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    # výška tabulky: lokální ticky i ticky došlé z remote sloupců
    max_seq = max([state.get("seq", 0)] + [hh.last_seq for hh in hosts])
    now = time.monotonic()

    # Přirozená šířka sloupce podle obsahu (název hosta / "TIMEOUT" / rtt),
    # NEroztahujeme na celou šířku terminálu — vpravo zůstane mezera.
    # Pokud se to nevejde, sloupce zúžíme, aby se vešly.
    natural = max(9, min(20, max(len(h.label) for h in hosts) + 1))
    fit = (w - SEQW - 1) // len(hosts)
    colw = max(9, min(natural, fit))
    table_w = min(w, SEQW + colw * len(hosts))

    # svislé rozvržení (odspodu): nápověda, řádky metrik, oddělovač, tabulka.
    sep_y = h - 2 - len(METRICS)     # řádek s oddělovačem statistik
    nrows = max(1, sep_y - 3)        # kolik řádků tabulky se vejde nad oddělovač

    # Řádky tabulky: každý tick = jeden zarovnaný řádek, a hned pod ním
    # případné plnošířkové řádky s detailem negativní odpovědi. Sbíráme jen
    # potřebné okno odspodu (od nejnovějšího) — O(viditelné řádky), ne O(historie).
    total = max_seq + sum(host.neg for host in hosts)
    scroll_off = min(state.get("scroll_off", 0), max(0, total - nrows))
    state["scroll_off"] = scroll_off
    state["nrows"] = nrows
    state["total_rows"] = total

    need = scroll_off + nrows
    rows_bottom_up: list = []          # index 0 = úplně spodní řádek
    seq = max_seq
    while seq >= 1 and len(rows_bottom_up) < need:
        block = [("tick", seq)]        # v pořadí top→bottom
        for host in hosts:
            p = host.pings.get(seq)
            if p and p.detail:
                block.append(("detail", seq, host.label, p.detail))
        for r in reversed(block):      # detaily odspodu, pak tick
            rows_bottom_up.append(r)
        seq -= 1
    visible = list(reversed(rows_bottom_up[scroll_off:scroll_off + nrows]))

    # titulek
    title = (f" TUI ping — {len(hosts)} adres · interval {state['interval']}s"
             f" · timeout {state['timeout']}s · {state.get('method', '')} ")
    stdscr.addnstr(0, 0, title.ljust(w), w, curses.A_BOLD | curses.A_REVERSE)

    # hlavička s adresami
    header = "ping".rjust(SEQW)
    for host in hosts:
        header += host.label[:colw - 1].rjust(colw)
    stdscr.addnstr(2, 0, header, table_w, curses.A_BOLD | curses.A_UNDERLINE)

    # datové řádky, nejnovější dole
    for i, item in enumerate(visible):
        y = 3 + i
        if y >= sep_y:
            break
        if item[0] == "tick":
            seq = item[1]
            stdscr.addnstr(y, 0, f"#{seq}".rjust(SEQW), SEQW, curses.A_DIM)
            x = SEQW
            for host in hosts:
                txt, color = cell_text(host.pings.get(seq), colw, now)
                attr = curses.color_pair(color) if color else 0
                if txt:
                    stdscr.addnstr(y, x, txt.rjust(colw), colw, attr)
                x += colw
        else:  # plnošířkový vložený řádek s detailem negativní odpovědi
            _, seq, label, detail = item
            line = f"  ⚠ #{seq} {label}: {detail}"
            stdscr.addnstr(y, 0, line[:w - 1].ljust(w - 1), w - 1,
                           curses.color_pair(RED))

    # ── oddělovač + řádky metrik (zarovnané do stejných sloupců jako pingy) ──
    if sep_y >= 3:
        stdscr.addnstr(sep_y, 0, "─" * table_w, table_w, curses.A_DIM)
        for j, (label, fn, colorfn) in enumerate(METRICS):
            y = sep_y + 1 + j
            if y >= h - 1:
                break
            stdscr.addnstr(y, 0, label.rjust(SEQW), SEQW,
                           curses.A_BOLD | curses.A_DIM)
            x = SEQW
            for host in hosts:
                val = fn(host).rjust(colw)
                stdscr.addnstr(y, x, val, colw,
                               curses.color_pair(colorfn(host)))
                x += colw

    # nápověda na posledním řádku
    elapsed = time.monotonic() - start_ts
    live = "živě" if scroll_off == 0 else f"↑{scroll_off}"
    hint = f"[{elapsed:.0f}s]  q=konec  ↑/↓=scroll  home/end=okraje  [{live}]"
    stdscr.addnstr(h - 1, 0, hint.ljust(w - 1), w - 1, curses.A_DIM)
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


# ── zapojení do curses ────────────────────────────────────────────────────────

async def amain(stdscr, hosts, args) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)    # ok
    curses.init_pair(2, curses.COLOR_RED, -1)      # chyba
    curses.init_pair(3, curses.COLOR_YELLOW, -1)   # pending / timeout

    # vyber pinger (nativní ICMP socket, nebo subprocess fallback)
    global PINGER
    PINGER = build_pinger(args.subprocess, args.cmd)
    _assign_probers(hosts)
    state = {
        "quit": False, "seq": 0, "scroll_off": 0, "dirty": asyncio.Event(),
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
    """Lokálním cílům bez sondy přiřadí ICMP sondu (DNS už mají z parse_spec)."""
    for h in hosts:
        if not h.transport and h.prober is None:
            h.prober = IcmpProbe(h.addr)


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
    state = {"quit": False, "seq": 0, "emit": _emit, "dirty": None}
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
    colw = max(9, max(len(h.label) for h in hosts) + 1)
    color = sys.stdout.isatty()

    now = time.monotonic()
    R, B, DIM = "\x1b[0m", "\x1b[1m", "\x1b[2m"
    YEL, GRN, RED = "\x1b[33m", "\x1b[32m", "\x1b[31m"
    # mapování barevného páru (viz lat_color/loss_color) na ANSI kód
    ANSI = {0: "", GREEN: GRN, YELLOW: YEL, 2: RED}

    def cell(p: Ping | None) -> str:
        if p is None:
            return "-".rjust(colw)
        if p.status == OK:
            txt = (f"{p.rtt:.0f}ms/{_fmt_ttl(p.ttl)}" if p.ttl is not None
                   else f"{p.rtt:.1f}ms")
            txt, col = txt.rjust(colw), ANSI[lat_color(p.rtt)]
        elif p.status == ERROR:
            txt, col = (p.msg or "ERR")[:colw - 1].rjust(colw), RED
        elif p.status == TIMEOUT or now - p.created >= TIMEOUT_X:
            txt, col = "- - -".center(colw), YEL   # timeout: žlutě jako nedoručeno
        else:
            txt, col = "· · ·".center(colw), YEL
        return f"{col}{txt}{R}" if color else txt

    def c(s: str, code: str) -> str:
        return f"{code}{s}{R}" if color else s

    print()
    print(c("Historie pingů:", B))
    header = "ping".rjust(7) + "".join(h.label[:colw - 1].rjust(colw) for h in hosts)
    print(c(header, B))
    print(c("─" * len(header), DIM))
    for seq in range(1, max_seq + 1):
        row = c(f"#{seq}".rjust(7), DIM)
        for host in hosts:
            row += cell(host.pings.get(seq))
        print(row)
        # plné detaily negativních odpovědí (unreachable, DNS, …) inline pod tickem
        for host in hosts:
            p = host.pings.get(seq)
            if p and p.detail:
                print(c(f"  ⚠ #{seq} {host.label}: {p.detail}", RED))
    print(c("─" * len(header), DIM))
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


def main() -> None:
    ap = argparse.ArgumentParser(description="TUI ping na více adres najednou.")
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

    hosts = [parse_spec(s) for s in args.hosts]
    if args.json:
        run_json(hosts, args)
        return
    curses.wrapper(run, hosts, args)
    print_history(hosts)      # po ukončení TUI zůstane historie v terminálu


if __name__ == "__main__":
    main()
