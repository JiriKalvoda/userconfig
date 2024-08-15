#!/usr/bin/env python3
import sys, os, pathlib
import subprocess
import functools
import argparse
import tabulate

@functools.cache
def name_to_path(name, prefix_path=pathlib.Path(".")):
    if name == "":
        if prefix_path.is_dir():
            if (prefix_path/"init.sh").is_file():
                return prefix_path/"init.sh"
        if prefix_path.is_file():
            return prefix_path
        return None
    name = name.split("-")
    variants = []
    for i in range(1, len(name)+1):
        p = prefix_path/("-".join(name[:i]))
        if p.is_dir() or (p.is_file() and i == len(name)):
            variants.append(("-".join(name[i:]), p))
    # print(name, prefix_path, variants)
    if len(variants) == 0:
        return None
    assert len(variants) == 1, (name, prefix_path, variants)
    return name_to_path(*variants[0])

@functools.cache
def current_version(name):
    if name_to_path(name) is None: return None
    p = subprocess.run([name_to_path(name), "-v"], encoding="utf-8", check=True, stdout=subprocess.PIPE)
    return p.stdout.strip()

@functools.cache
def is_sysconfig(name):
    if name_to_path(name) is None: return None
    p = subprocess.run([name_to_path(name), "-t"], encoding="utf-8", check=True, stdout=subprocess.PIPE)
    return p.stdout.strip() == 'sysconfig'

def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


class Log:
    def __init__(self, state_dir, name, logname):
        self.state_dir = state_dir
        self.name = name
        self.logname = logname
        self.dir = state_dir/name/logname
        self.state = read(self.dir/"state")
        self.version = read(self.dir/"version") or "0"
        self.date = read(self.dir/"date")
        self.args = " ".join((read(self.dir/"args") or "").split(" ")[1:])

class Installation:
    def __init__(self, state_dir, name):
        self.state_dir = state_dir
        self.name = name
        self.dir = state_dir/name

    @functools.cache
    def last(self):
        try:
            l = (self.dir/"last").readlink()
        except FileNotFoundError:
            return None
        return Log(self.state_dir, self.name, l)

    @functools.cache
    def last_ok(self):
        l = (self.dir/"last").readlink()
        return Log(self.state_dir, self.name, l)

    def short(self):
        v = self.last().version
        s = self.last().state
        cv = current_version(self.name)
        v_if_n_curr = v if v != cv else ""
        if s == "ok":
            if v == cv:
                return f"\033[92mOK\033[39m"
            else:
                return f"\033[93m{v}\033[39m"
        elif s == "faild":
            return f"\033[91mF{v_if_n_curr}\033[39m"
        elif s == "installing":
            return f"\033[91mI{v_if_n_curr}\033[39m"
        else:
            return f"\033[91m{s} {v_if_n_curr}\033[39m"



def load_state_dir(state_dir=pathlib.Path("state")):
    out = {}
    for i in state_dir.iterdir():
        if i.is_dir():
            name = i.name
            out[name] = Installation(state_dir, name)
    return out

parser = argparse.ArgumentParser()
parser.add_argument('--server', '-s', action='store_true')
parser.add_argument('--filter-devices', '-f')
parser.add_argument('--filter-scripts', '-F')

args = parser.parse_args()


if args.server:
    devices = []
    p = pathlib.Path("../userconfig_state")
    if args.filter_devices:
        filter_devices = eval("lambda u, m: "+args.filter_devices)
    else:
        filter_devices = None
    for i in p.iterdir():
        device = i.name
        if not filter_devices or filter_devices(*device.split("@")):
            devices.append((device, load_state_dir(i/"state")))
    devices.sort(key=lambda x: list(reversed(x[0].split("@"))))
    all_names = set()
    for name, i in devices:
        for j in i:
            if i[j].last():
                all_names.add(j)
    if args.filter_scripts:
        f = eval("lambda x: "+args.filter_scripts)
        all_names = {x for x in all_names if f(x)}
    all_names = list(all_names)
    all_names.sort()
    table = [[name, current_version(name)] + [i[name].short() if name in i and i[name].last() else "." for  dev_name, i in devices] for name in all_names]
    head_mach = ["", "v"]
    head_user = ["", "" ]
    for name, i in devices:
        u, m = name.split("@")
        head_mach.append(m[:5])
        head_user.append("jiklv" if u == "jirikalvoda" else u)
    head = [head_mach, head_user, tabulate.SEPARATING_LINE]
    print(tabulate.tabulate(head+table))
else:
    local = load_state_dir()
    table = [[name, name_to_path(name), local[name].last().args, current_version(name), local[name].last_ok().version,  local[name].short(), local[name].last().date] for name in sorted(local) if local[name].last()]
    print(tabulate.tabulate([["Name", "Path","args", "cv", "iv", "state", "date"], tabulate.SEPARATING_LINE]+table))
