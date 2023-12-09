#!/usr/bin/env python3
import asyncio
import aioconsole
import time
import subprocess
import os

def get_t():
    return int(time.monotonic())

data = []

async def get_from_conntrack():
    proc = await asyncio.create_subprocess_exec( 
        "conntrack", '-E',  '-o', 'save', '-e', 'DESTROY',
        stdout=asyncio.subprocess.PIPE)
    print("START", flush=True)
    while True:
        l = await proc.stdout.readline()
        if b" ::1 " in l or b" 127.0.0.1 " in l:
            continue
        data.append((get_t(), l))

async def garbage_colector():
    while True:
        await asyncio.sleep(60)
        ct = get_t()
        global data
        before = len(data)
        data = [(t,v) for t,v in data if t > ct - 5*60]
        after = len(data)
        print(f"GC: {before} -> {after}", flush=True)

def reinsert(max_delay=15, timeout=60):
    global data
    data_insert, data_else = [], []
    ct = get_t()
    for t,v in data:
        (data_else, data_insert)[t > ct - max_delay].append((t,v))
    p = subprocess.Popen(['conntrack', '--load-file', '-'], stdin=subprocess.PIPE)
    stdin = b''.join(b"-A -t 60 "+v[2:] for t,v in data_insert)
    print(stdin, flush=True)
    p.communicate(input=stdin)
    data_else = data
    print("DONE", flush=True)



async def client(reader, writer):
    ch = await reader.read(1)
    print("INPUT", ch, flush=True)
    if ch == b'R':
        reinsert(max_delay=15)
    if ch == b'A':
        reinsert(max_delay=5*60)
    await writer.drain()

os.umask(0o077)
sock_path = "/run/conntrack_hack"
try:
    os.remove(sock_path)
except FileNotFoundError:
    ...

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(
    get_from_conntrack(),
    garbage_colector(),
    asyncio.start_unix_server(client, sock_path)
))
