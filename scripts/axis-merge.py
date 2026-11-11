#!/usr/bin/env python3
r"""
POUZITI (ukazky):

  # live sledovani: 6 spojeni na kameru, 3 s za realitou, 1 pixel videa = 1 pixel displeje
  ./axis-merge.py --url 'http://10.0.0.41/axis-cgi/mjpg/video.cgi?resolution=720x576' --conns 6 --delay 3 \
      | mpv --untimed --cache-pause=no --video-unscaled=yes -

  # Potažmo 10.0.0.40 pro druhou kameru

  # live sledovani + zaroven nahravani do Matrosky (vsechny snimky, i ty pro live opozdene)
  ./axis-merge.py --url 'http://10.0.0.41/axis-cgi/mjpg/video.cgi?resolution=720x576' --conns 6 --delay 3 \
      --record 'rec-%Y%m%d-%H%M%S.mkv' | mpv --untimed --cache-pause=no --video-unscaled=yes -

  # jen nahravat (bez live vystupu), zapis 10 s za realitou
  ./axis-merge.py --url 'http://10.0.0.41/axis-cgi/mjpg/video.cgi?resolution=720x576' --conns 6 \
      --no-live --record 'rec-%Y%m%d-%H%M%S.mkv' --record-delay 10

  # sledovat nahravku, ktera se prave stavi (mpv na konci ceka na dalsi data; End = skok na aktualni konec)
  mpv --video-unscaled=yes appending://rec-20261111-121500.mkv

  # prehrat hotovou nahravku (bezny soubor se spravnym casovanim a seekovanim)
  mpv rec-20261111-121500.mkv

  # surova MJPEG nahravka (--record x.mjpg) se prehrava pres --play, 4x rychleji od 10. minuty
  ./axis-merge.py --play zaznam.mjpg --speed 4 --start 600 | mpv --untimed -

CO TO DELA:

axis-merge.py slouci nekolik paralelnich MJPEG spojeni na Axis kameru
do jednoho MJPEG streamu na stdout, serazeneho a odduplikovaneho podle
casove znacky, kterou Axis vklada do kazdeho JPEG (segment COM).
Duvod: kamera (nebo linka) omezuje propustnost na jedno TCP spojeni,
vice spojeni dohromady dorucuje vice ruznych snimku.

Vystup je pacovan podle znacek kamery s pevnym zpozdenim, takze se
prehrava puvodni rychlosti, jen o --delay sekund pozdeji nez live.
mpv se spousti s --untimed (zobrazi snimek hned, jak dorazi, casovani
dela tento skript) a --cache-pause=no (pri mezere neceka na doplneni cache).

Nahravani a prehravani:
  --record FILE.mkv    paralelne s live vystupem uklada VSECHNY prijate snimky
                       do Matrosky: MJPEG beze zmeny, kazdy snimek s casovou
                       znackou podle hodin kamery -> mpv/VLC/ffmpeg prehraji
                       primo, spravnou rychlosti, se seekovanim. Zapis ma
                       prodlevu --record-delay (default 30 s), takze se ulozi
                       i snimky, ktere pro live dorazily prilis pozde.
                       Jmeno muze obsahovat strftime (rec-%Y%m%d-%H%M%S.mkv);
                       existujici soubor se neprepise, novy dostane priponu s casem.
                       Rozestaveny soubor lze sledovat uz behem nahravani:
                       mpv appending://zaznam.mkv   (na konci ceka na dalsi data;
                       zpozdeni za live = --record-delay + ~2 s, zpet lze seekovat)
  --record FILE.mjpg   totez jako surovy multipart MJPEG (pripojuje na konec);
                       prehrat lze jen pres --play (mpv samo nezna casovani)
  --no-live --record F jen nahravat, nic na stdout
  --play FILE.mjpg     prehrat surovou nahravku s puvodnim casovanim:
                       ./axis-merge.py --play zaznam.mjpg | mpv --untimed -
                       (--speed 2 = 2x rychleji, --start 600 = od 10. minuty)

Statistiky (stderr, kazdych --stats sekund, vzdy za uplynuly interval):
  fps 7.3 | in 123 dup 54 late 2/1 | lat 0.82+-0.31 max 1.95 | anc +0.03 | q 22/2.1s | gap 48 15 5 3 2 0 | c 24 24 22 19 22 36
   fps   prumerne odvysilane snimky za sekundu
   in    prijato snimku ze vsech spojeni celkem
   dup   z toho duplicit (stejna znacka kamery uz prisla jinym spojenim)
   late  prislo az po case, kdy mely byt odvysilany / z toho zahozeno,
         protoze uz byl odvysilan novejsi snimek
   lat   zpozdeni prichodu snimku vuci kotve (s): stredni hodnota
         +- smerodatna odchylka a maximum za interval; kotva = nejrychlejsi
         prichod za poslednich --anchor-window s, takze lat rika, o kolik
         pozdeji nez "nejlepsi mozny" snimek dorazil; --delay by mel byt
         vetsi nez 'max' (nebo stred + 3 odchylky), jinak snimky chodi pozde
   anc   posun kotvy za interval (s): + zpozdeni za live vzrostlo (linka se
         zhorsila nebo hodiny kamery driftuji), - zpozdeni se zkratilo
   q     snimku ve fronte / casovy rozsah fronty v sekundach (~ aktualni zpozdeni)
   gap   histogram prodlev mezi odvysilanymi snimky (podle znacek kamery),
         sloupce: <100 <200 <300 <500 <1000 >=1000 ms
   c     snimku prijatych z jednotlivych spojeni (! = spojeni prave neni pripojeno)
   rec   (jen s --record) do souboru zapsano / zahozeno, protoze dorazily
         pozdeji nez --record-delay; q = snimku cekajicich na zapis
"""
import argparse
import heapq
import http.client
import os
import struct
import sys
import threading
import time
from collections import deque
from urllib.parse import urlsplit

OUT_BOUNDARY = b"--axismerge"


def log(msg):
    sys.stderr.write(f"[axis-merge] {msg}\n")
    sys.stderr.flush()


# ---------------------------------------------------------------- JPEG parsing

def axis_timestamp(jpeg):
    """Vrati casovou znacku z Axis COM segmentu (sekundy jako float), nebo None.
    Format: 0a 01 <4B unix sec BE> <1B setiny> <4B sec> <1B setiny> 01"""
    i = 2
    n = len(jpeg)
    while i + 4 <= n and jpeg[i] == 0xFF:
        marker = jpeg[i + 1]
        if marker == 0xD8:
            i += 2
            continue
        if marker == 0xDA:  # SOS - dal uz jen data
            break
        seg_len = int.from_bytes(jpeg[i + 2:i + 4], "big")
        if marker == 0xFE and seg_len >= 9:
            seg = jpeg[i + 4:i + 2 + seg_len]
            if seg[0] == 0x0A and seg[1] == 0x01 and seg[6] < 100:
                secs = int.from_bytes(seg[2:6], "big")
                return secs + seg[6] / 100.0
        i += 2 + seg_len
    return None


# ------------------------------------------------------------ MJPEG reader

def iter_mjpeg(f, boundary, stop=None):
    """Generator JPEG snimku z multipart MJPEG streamu (file-like s readline/read).
    Konci pri EOF nebo kdyz je nastaven stop (threading.Event)."""
    while stop is None or not stop.is_set():
        headers = {}
        line = f.readline()
        if not line:
            return
        line = line.strip()
        if not line or line.startswith(boundary):
            # boundary / prazdny radek -> nasleduji hlavicky casti
            pass
        elif b":" in line:
            k, v = line.split(b":", 1)
            headers[k.strip().lower()] = v.strip()
        else:
            continue
        while True:
            line = f.readline()
            if not line:
                return
            line = line.strip()
            if not line:
                break
            if b":" in line:
                k, v = line.split(b":", 1)
                headers[k.strip().lower()] = v.strip()
        if not headers:
            continue
        clen = headers.get(b"content-length")
        if clen is not None:
            body = f.read(int(clen))
            if len(body) != int(clen):
                return
        else:
            buf = bytearray()
            while True:
                l2 = f.readline()
                if not l2:
                    return
                if l2.strip().startswith(boundary):
                    break
                buf += l2
            body = bytes(buf).rstrip(b"\r\n")
        if body.startswith(b"\xff\xd8"):
            yield body


def mjpeg_boundary(content_type, default=b"--myboundary"):
    for part in content_type.split(";"):
        part = part.strip()
        if part.lower().startswith("boundary="):
            b = part.split("=", 1)[1].strip('"')
            if not b.startswith("--"):
                b = "--" + b
            return b.encode()
    return default


class Reader(threading.Thread):
    def __init__(self, idx, url, merger, timeout):
        super().__init__(daemon=True, name=f"conn{idx}")
        self.idx = idx
        self.url = url
        self.merger = merger
        self.timeout = timeout
        self.frames = 0
        self.alive = False

    def run(self):
        backoff = 0.5
        while not self.merger.stop.is_set():
            try:
                self.stream()
                backoff = 0.5
            except Exception as e:  # noqa: BLE001
                self.alive = False
                log(f"{self.name}: {e.__class__.__name__}: {e}; reconnect in {backoff:.1f}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)

    def stream(self):
        u = urlsplit(self.url)
        cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
        conn = cls(u.hostname, u.port, timeout=self.timeout)
        path = u.path + ("?" + u.query if u.query else "")
        conn.request("GET", path, headers={"User-Agent": "axis-merge/1.0"})
        resp = conn.getresponse()
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} {resp.reason}")
        bbytes = mjpeg_boundary(resp.getheader("Content-Type", ""))
        self.alive = True
        for body in iter_mjpeg(resp, bbytes, self.merger.stop):
            self.frames += 1
            self.merger.push(body, self.idx)
        if not self.merger.stop.is_set():
            raise ConnectionError("stream ended")


# ---------------------------------------------------------------- merger

class Merger:
    """Slucuje snimky z vice spojeni, radi podle znacky kamery a vypousti je
    s pevnym zpozdenim --delay za "nejcerstvejsim moznym" prichodem.

    Mapovani hodin kamery na lokalni cas (kotva) = minimum z (cas prichodu -
    znacka kamery) za poslednich --anchor-window sekund, tj. podle snimku,
    ktere dorazily nejrychleji. Kotva se k cilove hodnote posouva omezenou
    rychlosti (--catchup dolu, 4x rychleji nahoru), aby zpozdeni nerostlo
    driftem hodin ani jednorazovou spickou latence a aby se zkracovalo
    plynule (prehravani o par procent rychleji), ne skokem."""

    def __init__(self, delay, pace, out, anchor_window=60.0, catchup=0.05,
                 rec_out=None, rec_delay=30.0):
        self.delay = delay
        self.pace = pace
        self.out = out
        self.rec_out = rec_out          # soubor pro nahravani (nebo None)
        self.rec_delay = rec_delay
        self.rec_heap = []
        self.rec_last_ts = -1.0
        self.stat_rec = 0
        self.stat_rec_drop = 0
        self.anchor_window = anchor_window
        self.catchup = catchup
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)
        self.heap = []            # (ts, seq, jpeg)
        self.seq = 0
        self.seen = set()
        self.seen_order = deque()
        self.last_out_ts = -1.0
        # kotva: wall - ts pro "nejcerstvejsi" snimky
        self.anchor = None
        self.anchor_last_update = None
        self.buckets = deque()    # (sekunda, min(wall - ts) v te sekunde)
        # statistiky za interval
        self.stat_in = 0
        self.stat_dup = 0
        self.stat_late = 0
        self.stat_late_drop = 0
        self.stat_out = 0
        self.stat_nots = 0
        self.last_wall_ts = None
        self.hist_edges = (0.1, 0.2, 0.3, 0.5, 1.0)
        self.hist = [0] * (len(self.hist_edges) + 1)
        self.prev_out_ts = None
        self.lat_n = 0
        self.lat_sum = 0.0
        self.lat_sq = 0.0
        self.lat_max = None
        self.anchor_shift = 0.0

    # --- kotva -----------------------------------------------------------

    def note_arrival(self, now, ts):
        """Zapise prichod snimku do minutovych kosu a vrati cilovou kotvu."""
        raw = now - ts
        sec = int(now)
        if self.buckets and self.buckets[-1][0] == sec:
            if raw < self.buckets[-1][1]:
                self.buckets[-1] = (sec, raw)
        else:
            self.buckets.append((sec, raw))
        while self.buckets and self.buckets[0][0] < sec - self.anchor_window:
            self.buckets.popleft()
        return min(b[1] for b in self.buckets)

    def update_anchor(self, now):
        """Posune kotvu smerem k cili omezenou rychlosti. Volat pod zamkem."""
        if self.anchor is None or not self.buckets:
            return
        target = min(b[1] for b in self.buckets)
        dt = now - self.anchor_last_update
        self.anchor_last_update = now
        if dt <= 0:
            return
        diff = target - self.anchor
        if diff < 0:
            step = max(diff, -self.catchup * dt)        # zkracovani zpozdeni
        else:
            step = min(diff, 4 * self.catchup * dt)     # prodluzovani zpozdeni
        self.anchor += step
        self.anchor_shift += step

    def out_time(self, ts):
        return self.anchor + self.delay + ts

    # --- prijem ----------------------------------------------------------

    def push(self, jpeg, src):
        ts = axis_timestamp(jpeg)
        with self.cv:
            now = time.time()
            self.stat_in += 1
            if ts is None:
                # bez znacky: pouzij lokalni cas, ale pouze rostouci
                self.stat_nots += 1
                ts = now
                if self.last_wall_ts is not None and ts <= self.last_wall_ts:
                    ts = self.last_wall_ts + 0.001
                self.last_wall_ts = ts
            key = round(ts * 100)
            if key in self.seen:
                self.stat_dup += 1
                return
            self.seen.add(key)
            self.seen_order.append(key)
            while len(self.seen_order) > 5000:
                self.seen.discard(self.seen_order.popleft())
            target = self.note_arrival(now, ts)
            if self.anchor is None:
                self.anchor = target
                self.anchor_last_update = now
            lat = (now - ts) - self.anchor
            self.lat_n += 1
            self.lat_sum += lat
            self.lat_sq += lat * lat
            self.lat_max = lat if self.lat_max is None else max(self.lat_max, lat)
            if lat > self.delay:
                self.stat_late += 1
            if self.rec_out is not None:
                if ts > self.rec_last_ts:
                    heapq.heappush(self.rec_heap, (ts, self.seq, jpeg))
                else:
                    self.stat_rec_drop += 1
            if ts <= self.last_out_ts:
                self.stat_late_drop += 1
                return
            self.seq += 1
            heapq.heappush(self.heap, (ts, self.seq, jpeg))
            self.cv.notify()

    # --- vystup ----------------------------------------------------------

    @staticmethod
    def mjpeg_part(jpeg):
        return (OUT_BOUNDARY + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")

    def record_due(self, now=None):
        """Zapise do souboru vsechny snimky, jejichz nahravaci cas uz nastal
        (now=None -> vsechny). Volat pod zamkem."""
        if self.rec_out is None:
            return
        while self.rec_heap:
            ts = self.rec_heap[0][0]
            if now is not None and self.anchor + self.rec_delay + ts > now:
                break
            _, _, jpeg = heapq.heappop(self.rec_heap)
            self.rec_out.write_frame(ts, jpeg)
            self.rec_last_ts = ts
            self.stat_rec += 1

    def flush_record(self):
        with self.lock:
            self.record_due(None)
            if self.rec_out is not None:
                self.rec_out.flush()

    def write_frame(self, jpeg, ts):
        if self.prev_out_ts is not None:
            gap = ts - self.prev_out_ts
            b = 0
            while b < len(self.hist_edges) and gap >= self.hist_edges[b]:
                b += 1
            self.hist[b] += 1
        self.prev_out_ts = ts
        self.out.write(self.mjpeg_part(jpeg))
        self.out.flush()
        self.stat_out += 1

    def run(self, readers, stats_every):
        if stats_every < 1e8:
            log(f"statistiky kazdych {stats_every:g}s: fps=odvysilano/s | in=prijato dup=duplicit "
                f"late=po case vysilani/z toho zahozeno | lat=zpozdeni prichodu vuci kotve "
                f"stred+-odchylka max [s], --delay > max | anc=posun kotvy za interval [s] "
                f"(+ = zpozdeni roste) | q=fronta snimku/sekund | "
                f"gap=prodlevy mezi odvysilanymi snimky: <100 <200 <300 <500 <1000 >=1000 ms | "
                f"c=snimku ze spojeni 1..{len(readers)} (!=odpojeno)"
                + (" | rec=do souboru zapsano/zahozeno (prisly pozdeji nez --record-delay) "
                   "q=snimku cekajicich na zapis" if self.rec_out is not None else ""))
        next_stats = time.time() + stats_every
        prev_out = 0
        while not self.stop.is_set():
            jpeg = None
            with self.cv:
                if not self.heap:
                    self.cv.wait(timeout=0.2)
                if self.heap:
                    ts, _, cand = self.heap[0]
                    if self.pace:
                        self.update_anchor(time.time())
                        wait = self.out_time(ts) - time.time()
                        if wait > 0:
                            self.cv.wait(timeout=min(wait, 0.2))
                        else:
                            heapq.heappop(self.heap)
                            jpeg = cand
                    else:
                        heapq.heappop(self.heap)
                        jpeg = cand
                if jpeg is not None:
                    self.last_out_ts = ts
                if self.rec_out is not None and self.anchor is not None:
                    self.record_due(time.time())
            if jpeg is not None and self.out is not None:
                try:
                    self.write_frame(jpeg, ts)
                except BrokenPipeError:
                    log("stdout uzavren (prehravac skoncil)")
                    if self.rec_out is None:
                        self.stop.set()
                        return
                    self.out = None
            now = time.time()
            if now >= next_stats:
                with self.lock:
                    per = " ".join(f"{r.frames}{'' if r.alive else '!'}" for r in readers)
                    for r in readers:
                        r.frames = 0
                    backlog = (self.heap[-1][0] - self.heap[0][0]) if len(self.heap) > 1 else 0.0
                    nots = f" nots {self.stat_nots}" if self.stat_nots else ""
                    rec = f" | rec {self.stat_rec}/{self.stat_rec_drop} q {len(self.rec_heap)}" if self.rec_out is not None else ""
                    if self.lat_n:
                        mean = self.lat_sum / self.lat_n
                        var = max(self.lat_sq / self.lat_n - mean * mean, 0.0)
                        lat = f"lat {mean:.2f}+-{var ** 0.5:.2f} max {self.lat_max:.2f}"
                    else:
                        lat = "lat -"
                    log(f"fps {(self.stat_out - prev_out) / stats_every:4.1f} | in {self.stat_in:3d} "
                        f"dup {self.stat_dup:3d} late {self.stat_late}/{self.stat_late_drop}{nots} | {lat} | "
                        f"anc {self.anchor_shift:+.2f} | q {len(self.heap)}/{backlog:.1f}s | "
                        f"gap {' '.join(str(h) for h in self.hist)} | c {per}{rec}")
                    prev_out = self.stat_out
                    self.stat_in = self.stat_dup = self.stat_late = self.stat_late_drop = self.stat_nots = 0
                    self.hist = [0] * len(self.hist)
                    self.lat_n = 0
                    self.lat_sum = self.lat_sq = 0.0
                    self.lat_max = None
                    self.anchor_shift = 0.0
                    self.stat_rec = self.stat_rec_drop = 0
                next_stats = now + stats_every


# ---------------------------------------------------------------- zapis souboru

def jpeg_size(jpeg):
    """(sirka, vyska) z SOF segmentu JPEGu, nebo None."""
    i = 2
    n = len(jpeg)
    while i + 4 <= n and jpeg[i] == 0xFF:
        m = jpeg[i + 1]
        if m == 0xD8:
            i += 2
            continue
        if m == 0xDA:
            break
        seg_len = int.from_bytes(jpeg[i + 2:i + 4], "big")
        if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
            h = int.from_bytes(jpeg[i + 5:i + 7], "big")
            w = int.from_bytes(jpeg[i + 7:i + 9], "big")
            return w, h
        i += 2 + seg_len
    return None


class MjpegFileWriter:
    """Surovy multipart MJPEG (stejny format jako stdout), pripojuje na konec."""

    def __init__(self, path):
        self.path = path
        self.f = open(path, "ab")

    def write_frame(self, ts, jpeg):
        self.f.write(Merger.mjpeg_part(jpeg))

    def flush(self):
        self.f.flush()

    def close(self):
        self.f.close()


def _vint(n):
    """EBML kodovani velikosti."""
    if n < 0x7F:
        return bytes([0x80 | n])
    if n < 0x3FFF:
        return (0x4000 | n).to_bytes(2, "big")
    if n < 0x1FFFFF:
        return (0x200000 | n).to_bytes(3, "big")
    if n < 0x0FFFFFFF:
        return (0x10000000 | n).to_bytes(4, "big")
    return (0x0100000000000000 | n).to_bytes(8, "big")


def _el(eid, data):
    return eid + _vint(len(data)) + data


def _uint(eid, v, width=None):
    if width is None:
        width = max(1, (v.bit_length() + 7) // 8)
    return _el(eid, v.to_bytes(width, "big"))


def _str(eid, s):
    return _el(eid, s.encode("utf-8"))


class MkvWriter:
    """Minimalni Matroska muxer: jedna video stopa V_MJPEG, kazdy snimek
    SimpleBlock s vlastni casovou znackou (ms). Pise clustery po ~5 s,
    pri zavreni doplni Cues (index pro seekovani) a Duration."""

    SEGMENT_UNKNOWN = b"\x01\xff\xff\xff\xff\xff\xff\xff"
    CLUSTER_MAX_MS = 2000

    def __init__(self, path):
        self.path = path
        self.f = open(path, "wb")
        self.ts0 = None
        self.last_ms = -1
        self.cluster = []          # [(ms, jpeg)]
        self.cluster_start_ms = 0
        self.cues = []             # [(ms, offset vuci zacatku dat segmentu)]
        self.frames = 0
        self.header_written = False

    def _write_header(self, w, h):
        f = self.f
        f.write(_el(b"\x1a\x45\xdf\xa3",
                    _uint(b"\x42\x86", 1) + _uint(b"\x42\xf7", 1) + _uint(b"\x42\xf2", 4)
                    + _uint(b"\x42\xf3", 8) + _str(b"\x42\x82", "matroska")
                    + _uint(b"\x42\x87", 4) + _uint(b"\x42\x85", 2)))
        f.write(b"\x18\x53\x80\x67" + self.SEGMENT_UNKNOWN)
        self.seg_data = f.tell()
        # SeekHead s pevnou velikosti (pozice 8 B), Cues se doplni pri zavreni
        seekhead_len = 4 + 1 + 3 * 21
        pos_info = seekhead_len
        info = (_uint(b"\x2a\xd7\xb1", 1000000) + _str(b"\x4d\x80", "axis-merge")
                + _str(b"\x57\x41", "axis-merge") + _el(b"\x44\x89", struct.pack(">d", 0.0)))
        info_el = _el(b"\x15\x49\xa9\x66", info)
        pos_tracks = pos_info + len(info_el)

        def seek(eid, pos):
            return _el(b"\x4d\xbb", _el(b"\x53\xab", eid) + _uint(b"\x53\xac", pos, 8))
        self.seekhead_pos = f.tell()
        # treti polozka je zatim Void (21 B), aby ctenar rozestaveneho souboru
        # nehledal Cues, ktere jeste neexistuji; pri close se prepise na Seek(Cues)
        f.write(_el(b"\x11\x4d\x9b\x74", seek(b"\x15\x49\xa9\x66", pos_info)
                    + seek(b"\x16\x54\xae\x6b", pos_tracks) + _el(b"\xec", b"\x00" * 19)))
        assert f.tell() - self.seg_data == pos_info
        self.duration_pos = f.tell() + len(info_el) - 8
        f.write(info_el)
        video = _uint(b"\xb0", w) + _uint(b"\xba", h)
        track = (_uint(b"\xd7", 1) + _uint(b"\x73\xc5", 1) + _uint(b"\x83", 1) + _uint(b"\x9c", 0)
                 + _str(b"\x86", "V_MJPEG") + _el(b"\xe0", video))
        f.write(_el(b"\x16\x54\xae\x6b", _el(b"\xae", track)))
        self.header_written = True

    def write_frame(self, ts, jpeg):
        if not self.header_written:
            size = jpeg_size(jpeg)
            if size is None:
                return
            self._write_header(*size)
            self.ts0 = ts
        ms = int(round((ts - self.ts0) * 1000))
        if ms <= self.last_ms:
            ms = self.last_ms + 1
        self.last_ms = ms
        if self.cluster and ms - self.cluster_start_ms >= self.CLUSTER_MAX_MS:
            self._flush_cluster()
        if not self.cluster:
            self.cluster_start_ms = ms
        self.cluster.append((ms, jpeg))
        self.frames += 1

    def _flush_cluster(self):
        if not self.cluster:
            return
        base = self.cluster_start_ms
        body = _uint(b"\xe7", base)
        for ms, jpeg in self.cluster:
            body += _el(b"\xa3", b"\x81" + (ms - base).to_bytes(2, "big", signed=True) + b"\x80" + jpeg)
        self.cues.append((base, self.f.tell() - self.seg_data))
        self.f.write(_el(b"\x1f\x43\xb6\x75", body))
        self.f.flush()
        self.cluster = []

    def flush(self):
        self.f.flush()

    def close(self):
        if not self.header_written:
            self.f.close()
            return
        self._flush_cluster()
        cues_pos = self.f.tell() - self.seg_data
        cues = b"".join(_el(b"\xbb", _uint(b"\xb3", ms)
                            + _el(b"\xb7", _uint(b"\xf7", 1) + _uint(b"\xf1", off)))
                        for ms, off in self.cues)
        self.f.write(_el(b"\x1c\x53\xbb\x6b", cues))
        end = self.f.tell()
        # doplneni: velikost segmentu, Duration, pozice Cues v SeekHead
        self.f.seek(self.seg_data - 8)
        self.f.write((0x0100000000000000 | (end - self.seg_data)).to_bytes(8, "big"))
        self.f.seek(self.duration_pos)
        self.f.write(struct.pack(">d", float(self.last_ms)))
        self.f.seek(self.seekhead_pos + 5 + 2 * 21)
        self.f.write(_el(b"\x4d\xbb", _el(b"\x53\xab", b"\x1c\x53\xbb\x6b") + _uint(b"\x53\xac", cues_pos, 8)))
        self.f.close()


def open_recorder(path):
    """Podle pripony: .mjpg/.mjpeg = surovy MJPEG (pripojuje), jinak Matroska
    (novy soubor; existujici jmeno dostane casovou priponu)."""
    path = time.strftime(path)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".mjpg", ".mjpeg"):
        return MjpegFileWriter(path), path
    if os.path.exists(path):
        root, e = os.path.splitext(path)
        path = f"{root}-{time.strftime('%Y%m%d-%H%M%S')}{e}"
    return MkvWriter(path), path


def play_file(path, out, speed=1.0, start=0.0, max_gap=2.0):
    """Prehraje nahrany MJPEG soubor na stdout s puvodnim casovanim podle
    znacek kamery. Mezery delsi nez max_gap (vypadky, konce relaci) zkrati."""
    n = 0
    t_first = None
    with open(path, "rb") as f:
        head = f.read(256)
        f.seek(0)
        boundary = head.split(b"\r\n", 1)[0].strip() if head.startswith(b"--") else OUT_BOUNDARY
        prev_ts = None
        wall = None
        for jpeg in iter_mjpeg(f, boundary):
            ts = axis_timestamp(jpeg)
            if ts is None:
                ts = prev_ts + 1.0 / 15 if prev_ts is not None else 0.0
            if t_first is None:
                t_first = ts
            if ts - t_first < start:
                prev_ts = ts
                continue
            if prev_ts is not None and wall is not None:
                gap = ts - prev_ts
                if gap < 0 or gap > max_gap:
                    gap = min(max(gap, 0.0), max_gap)
                wall += gap / speed
                delay = wall - time.time()
                if delay > 0:
                    time.sleep(delay)
            else:
                wall = time.time()
            prev_ts = ts
            try:
                out.write(Merger.mjpeg_part(jpeg))
            except BrokenPipeError:
                break
            n += 1
    log(f"prehrano {n} snimku")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="URL MJPEG streamu (video.cgi)")
    ap.add_argument("--record", metavar="FILE",
                    help="zaroven ukladat vsechny prijate snimky do souboru: .mkv (Matroska s casovymi "
                         "znackami, prehraje mpv primo; podporuje strftime, napr. rec-%%Y%%m%%d-%%H%%M%%S.mkv) "
                         "nebo .mjpg (surovy MJPEG, pripojuje; prehrat pres --play)")
    ap.add_argument("--record-delay", type=float, default=30.0,
                    help="prodleva zapisu do souboru (s); snimky, ktere dorazi pozdeji, se nezapisou (default 30)")
    ap.add_argument("--no-live", action="store_true", help="nic neposilat na stdout, jen nahravat")
    ap.add_argument("--play", metavar="FILE", help="prehrat nahrany soubor na stdout s puvodnim casovanim")
    ap.add_argument("--speed", type=float, default=1.0, help="rychlost prehravani souboru (default 1.0)")
    ap.add_argument("--start", type=float, default=0.0, help="prehravani: preskocit prvnich N sekund zaznamu")
    ap.add_argument("--max-gap", type=float, default=2.0,
                    help="prehravani: delsi mezery mezi snimky zkratit na N s (default 2)")
    ap.add_argument("--conns", type=int, default=4, help="pocet paralelnich spojeni (default 4)")
    ap.add_argument("--delay", type=float, default=3.0, help="zpozdeni za live v sekundach (default 3)")
    ap.add_argument("--no-pace", action="store_true", help="nevyckavat, posilat snimky hned (jen radit a dedup)")
    ap.add_argument("--anchor-window", type=float, default=60.0,
                    help="okno (s), ze ktereho se bere minimum zpozdeni jako kotva (default 60)")
    ap.add_argument("--catchup", type=float, default=0.05,
                    help="max. rychlost zkracovani zpozdeni v s za s, tj. 0.05 = prehravani o 5 %% rychleji (default 0.05)")
    ap.add_argument("--timeout", type=float, default=15.0, help="socket timeout (s)")
    ap.add_argument("--stats", type=float, default=10.0, help="interval statistik na stderr (s), 0 = vypnout (default 10)")
    ap.add_argument("--duration", type=float, default=0, help="skoncit po N sekundach (pro testy)")
    args = ap.parse_args()

    out = os.fdopen(sys.stdout.fileno(), "wb", buffering=0)
    if args.play:
        try:
            play_file(args.play, out, args.speed, args.start, args.max_gap)
        except KeyboardInterrupt:
            pass
        return
    if not args.url:
        ap.error("--url je povinne (nebo --play FILE)")
    if args.no_live and not args.record:
        ap.error("--no-live ma smysl jen s --record")
    rec_out = None
    if args.record:
        rec_out, rec_path = open_recorder(args.record)
        log(f"nahravam do {rec_path} (prodleva {args.record_delay:g}s)")
    merger = Merger(args.delay, not args.no_pace, None if args.no_live else out,
                    args.anchor_window, args.catchup, rec_out, args.record_delay)
    readers = [Reader(i + 1, args.url, merger, args.timeout) for i in range(args.conns)]
    for r in readers:
        r.start()
        time.sleep(0.05)
    if args.duration:
        threading.Timer(args.duration, merger.stop.set).start()
    try:
        merger.run(readers, args.stats if args.stats > 0 else 1e9)
    except KeyboardInterrupt:
        pass
    finally:
        merger.stop.set()
        if rec_out is not None:
            merger.flush_record()
            rec_out.close()
            log(f"nahravka uzavrena: {rec_path}")


if __name__ == "__main__":
    main()
