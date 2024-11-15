#!/bin/env python3

import subprocess
import argparse
import sys, os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("target")
parser.add_argument("-u", "--umount", action='store_true')
args = parser.parse_args()


param = args.target
dirname = param.split('--')[0]
mountpoint = os.environ['HOME']+"/m/"+dirname

if args.umount:
    if Path(mountpoint).exists():
        subprocess.run(["umount", mountpoint], check=True)
        os.rmdir(mountpoint)
    for x in os.listdir(os.environ['HOME']+"/m/"):
        if x.startswith(dirname):
            os.remove(os.environ['HOME']+"/m/"+x)
else:
    try:
        os.rmdir(mountpoint)
    except FileNotFoundError:
        pass

    server_mountpoint = "/"

    try:
        import blachlib.core
        namespace, m, rest = blachlib.core.find_by_name(param)
        server_mountpoint = m.sshfs_mountpoint
    except Exception as e:
        print(f"Loading blach configuration faield: {e}", file=sys.stderr)

    os.mkdir(mountpoint)
    follow_symlinks_args = ["-o", "follow_symlinks"]
    subprocess.run(["sshfs", *follow_symlinks_args, "-C", param+":"+server_mountpoint, mountpoint], check=True)

    remote_home = subprocess.run(["ssh", param, "pwd"], stdout=subprocess.PIPE).stdout.decode().strip()
    try:
        os.remove(mountpoint+"~")
    except FileNotFoundError:
        pass
    subprocess.run(["ln", "-sr", mountpoint+remote_home, mountpoint+"~"])
