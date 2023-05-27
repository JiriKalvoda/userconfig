#!/usr/bin/env python3
import sys, os
import subprocess
import tempfile
from pathlib import Path

from lib import *

print(sys.argv)

to_parse = sys.argv[1]
to_mpv = sys.argv[2:]

identificators = []

i = 0
while i < len(to_parse):
    if to_parse[i] in IDENTIFICATORS:
        identificators.append(IDENTIFICATORS[to_parse[i]])
    i += 1




with tempfile.TemporaryDirectory(dir = POINTERS_DIR) as pointer_dir:
    print('created temporary directory', pointer_dir)

    to_mpv = [f"--input-ipc-server={pointer_dir}/socket"] + to_mpv

    player_cmdline = ["mpv"] + to_mpv

    with open(Path(pointer_dir, "mp_cmdline"), "w") as f:
        f.write("\n".join(sys.argv) + "\n")
    with open(Path(pointer_dir, "player_cmdline"), "w") as f:
        f.write("\n".join(player_cmdline) + "\n")
    with open(Path(pointer_dir, "identificators"), "w") as f:
        f.write("\n".join(identificators) + "\n")

    with open(Path(pointer_dir, "status"), "w") as f:
        f.write("redy\n")
    subprocess.run(player_cmdline)


