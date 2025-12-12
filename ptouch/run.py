#!/bin/env python3
from pathlib import Path
import tempfile, sys, os, subprocess
import lib
d = Path("/".join(lib.__file__.split("/")[:-1]))

my_tty = open("/dev/tty")

def _getch(*question):
    import tty, termios
    print(*question, end="", flush=True)
    fd = my_tty.fileno()
    oldSettings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        answer = my_tty.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)
    print()
    return answer

def pre_exit():
    with open(tmpd+"/main.py", "r") as f:
        print()
        print()
        print(f.read())

with tempfile.TemporaryDirectory(prefix="label-maker-") as tmpd:
    with open(tmpd+"/main.py", "w+") as f:
        f.write("import sys\n")
        f.write(f"sys.path.append('{d}')\n")
        f.write("from lib import *\n")
        if not sys.stdin.isatty():
            f.write(sys.stdin.read())
            next_action = "run"
        else:
            next_action = "edit"
        f.flush()


        while True:
            match next_action:
                case "run":
                    r = subprocess.run(["python", f.name], stdin=open("/dev/tty"))
                    if r.returncode == 0:
                        pre_exit()
                        exit(0)
                    elif r.returncode == 42:
                        next_action = "edit"
                    else:
                        next_action = "user"
                case "edit":
                    r = subprocess.run(["vim", f.name, d/"lib.py"], stdin=open("/dev/tty"))
                    if r.returncode == 0:
                        next_action = "run"
                    else:
                        next_action = "user"
                case "user":
                    print("What next? [Edit/Run/Quit] ", end='', flush=True)
                    with open("/dev/stdout", "r") as my_tty:
                        #os.set_blocking(my_tty.fileno(), True)
                        #inp = my_tty.readline()[:1].lower()
                        inp = _getch()
                    if inp == 'e':
                        next_action = 'edit'
                    if inp == 'r':
                        next_action = 'run'
                    if inp == 'q':
                        pre_exit()
                        exit(0)



