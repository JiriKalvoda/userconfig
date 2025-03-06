#!/usr/bin/env python3
import time
import signal
import sys, os
import socket
import json
import subprocess

def p(*args):
    print(*args, flush=True)

def handler(signum, frame):
    signame = signal.Signals(signum).name
    p(f'Signal handler called with signal {signame} ({signum})')
signal.signal(signal.SIGHUP, handler)
signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGHUP])
p("PID", os.getpid())


sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

def ip(*args):
    if args[0] in [6, -6]:
        args = list(args)
        args[0] = "-6"
    r = subprocess.run(["ip", "-j", *args], stdout=subprocess.PIPE, encoding="utf-8")
    return json.loads(r.stdout) if r.stdout else None

def iwconfig():
    r = subprocess.run(["sh", "-c", "iwconfig  | jc --iwconfig"], stdout=subprocess.PIPE, encoding="utf-8")
    return json.loads(r.stdout) if r.stdout else None

def send(msg, target_ip):
    msg = json.dumps(msg).encode("utf-8")
    p(msg)
    sock.sendto(b"____01"+msg, (target_ip, 12011))

def format_ip(addr_info):
    return f"{addr_info['local']}/{addr_info['prefixlen']}"
def sort_ips(addrs):
    return addrs

while True:
    p("RUN")
    ipa = ip("a")
    iwc = {i["name"]: i for i in iwconfig()}

    def is_blatto(i):
        for ip in i["addr_info"]:
            if any(ip["local"].startswith(f"2a01:b380:3000:18{i}a:") for i in range(0, 10)):
                return True
        return False

    def is_blatto_wg(i):
        for ip in i["addr_info"]:
            if any(ip["local"].startswith(f"2a01:b380:3000:18{i}b:") for i in range(0, 10)):
                return True
        return False

    interfaces = {}
    blatto = False
    blatto_wg = False
    for i in ipa:
        if i["ifname"].startswith("qemu") or i["ifname"].startswith("ve22"):
            continue
        if i["operstate"] in ["UP", "UNKNOWN"]:
            out = {
                    "addr": [format_ip(ip) for ip in sort_ips(i["addr_info"])],
                    "mtu": i["mtu"]
                }

            if i["link_type"] == "ether": # WiFi or ethernet, no loopback or wireguard
                if is_blatto(i):
                   blatto = True

            if is_blatto_wg(i):
                   blatto_wg = {"mtu": i["mtu"]}


            if i["ifname"] in iwc:
                w = iwc[i["ifname"]]
                out["essid"] = w["essid"]
            interfaces[i["ifname"]] = out
    send({"blatto-wg": blatto_wg, "blatto": blatto, "interfaces": interfaces}, "2a01:b380:3000:181a::1" if blatto else "2a01:b380:3000:181b::1")
    p("DONE")
    signal.sigtimedwait([signal.SIGHUP], 10)
