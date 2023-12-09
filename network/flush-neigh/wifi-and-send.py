#!/usr/bin/python3
import socket
from time import sleep
import subprocess
import json
import sys, os

import syslog

subprocess.run(["wifi", sys.argv[1]])

import random

msg = f'hello {random.randrange(0,255)}'
sleep(1)
for i in range(300):
    p = subprocess.run(["ip", "-json", "a"], capture_output=True, encoding="utf-8")
    data = json.loads(p.stdout)
    ipv4 = [a["local"] for i in data for a in i["addr_info"] if a["family"]=="inet"]
    syslog.syslog(f"{ipv4}")
    for ip in ipv4:
        if ip.startswith("10.19.13"):
            sleep(1)
            syslog.syslog(f'sending on {ip} {msg}')
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            print(sock.bind((ip,0)))
            print(sock.sendto(msg.encode('utf-8'), ("10.19.13.255", 59423)))
            sock.close()
            syslog.syslog(f'done')
            exit(0)
    sleep(0.1)

exit(10)
