#!/usr/bin/env python3
import sys, os, pathlib
import subprocess
import functools

@functools.cache
def name_to_path(name, prefix_path=pathlib.Path(".")):
    if name == "":
        if prefix_path.is_dir():
            return prefix_path/"init.sh"
        return prefix_path
    name = name.split("-")
    variants = []
    for i in range(1, len(name)+1):
        p = prefix_path/("-".join(name[:i]))
        if p.exists():
            variants.append(("-".join(name[i:]), p))
    # print(name, prefix_path, variants)
    assert len(variants) == 1
    return name_to_path(*variants[0])

@functools.cache
def current_version(name):
    name_to_path(name)
    p = subprocess.run([name_to_path(name), "-v"], encoding="utf-8", check=True, stdout=subprocess.PIPE)
    return p.stdout.strip()

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

class Installation:
    def __init__(self, state_dir, name):
        self.state_dir = state_dir
        self.name = name
        self.dir = state_dir/name

    @functools.cache
    def last(self):
        l = (self.dir/"last").readlink()
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
        elif s == "fail":
            return "\033[91mF{v_if_n_curr}\033[39m"
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

local = load_state_dir()
table = [[name, local[name].short()] for name in local]


from tabulate import tabulate
print(tabulate(table))
