#!/bin/python3
import os, sys, subprocess
import time, select
import select

app_name = sys.argv[1] if len(sys.argv) >= 2 else None
session = None

def init():
    global session
    session = subprocess.Popen(["waydroid", "session", "start"], stderr=subprocess.PIPE)
    time.sleep(0.1)
    p = subprocess.run(["waydroid", "show-full-ui"])

def clean():
    subprocess.run(["waydroid", "session", "stop"])
    session.communicate()

init()
while True:
    poll = select.poll()
    poll.register(session.stderr.fileno(), select.POLLIN)
    poll.register(sys.stdin.fileno(), select.POLLIN)
    for fd, event in poll.poll():
        if fd == sys.stdin.fileno():
            inp = input()
            print("STDIN", inp)
            if inp == "reload":
                clean()
                init()
        if fd == session.stderr.fileno():
            print("SESSION")
            l = session.stderr.readline().strip().decode("utf-8")
            print(l)
            if l.endswith("Android with user 0 is ready"):
                if app_name:
                    p = subprocess.run(["waydroid", "app", "launch", app_name])
                    p = subprocess.run(["waydroid", "show-full-ui"])
