import socket
from time import sleep
import subprocess
import json

interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
allips = [ip[-1][0] for ip in interfaces]
print(allips)

msg = b'hello world'
for i in range(100):
    p = subprocess.run(["ip", "-json", "a"], capture_output=True, encoding="utf-8")
    data = json.loads(p.stdout)
    ipv4 = [a["local"] for i in data for a in i["addr_info"] if a["family"]=="inet"]
    print(ipv4)
    for ip in ipv4:
        if ip.startswith("10.19.13"):
            print(f'sending on {ip}')
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((ip,0))
            sock.sendto(msg, ("10.19.13.255", 5005))
            sock.close()
            exit(0)

    sleep(0.1)
exit(1)
