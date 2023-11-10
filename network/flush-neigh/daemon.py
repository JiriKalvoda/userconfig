import socket
import subprocess

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("0.0.0.0", 59423))
while True:
    data, addr = sock.recvfrom(1024)
    print(addr, data)
    subprocess.run(["ip", "neigh", "flush", addr[0]])

