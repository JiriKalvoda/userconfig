#!/usr/bin/env python3
import sys
import os
import osd
import threading
from collections import defaultdict

import Xlib
import Xlib.display
import Xlib.X

import argparse

import i3ipc
import time
import traceback
from dataclasses import dataclass

import signal

from i3_workspace_shared import *
from i3_workspace_lib import *
import i3_workspace_util as util
from i3_workspace_watch import i3_watch
from i3_workspace_constants import *
from typing import Any

main_functions = {}
main_functions_list = []

@dataclass
class MainFunction:
    names: Any
    args: Any
    f: Any
    help: Any

def arg(*args, **kvargs):
    return args, kvargs

def main_function(names, args, h):
    for name in names:
        assert name not in main_functions

    def lam(f):
        mf = MainFunction(names, args, f, h)
        main_functions_list.append(mf)
        for name in names:
            main_functions[name] = mf
        return f
    return lam


@main_function(["reload"], [], None)
def load(params):
    load_workspaces()


@main_function(["debug"], [], None)
def debug_print(params):
    print("output: ", output.output)
    print("master_on: ", output.master_on)
    print("slave_on: ", output.slave_on)
    print("slave_for: ", output.slave_for)
    print("slave_on_for: ", output.slave_on_for)
    print("output_of_workspace: ", output.output_of_workspace)

class EnumString(str):
    def options(self):
        pass
class WorkspaceType(EnumString):
    def options(self):
        return [workspace(*i) for i in WORKSPACES]
class MasterType(EnumString):
    def options(self):
        return [str(i) for i in range(MIN_MASTER, MAX_MASTER+1)] + ["next", "prev", "next-skip", "prev-skip", "alloc"]
class SlaveType(EnumString):
    def options(self):
        return [str(i) for i in range(MIN_SLAVE, MAX_SLAVE+1)] + ["next", "prev", "next-skip", "prev-skip", "next-limit", "prev-limit", "next-limit-skip", "prev-limit-skip", "alloc"]


std_parser = [
    arg('-m', "--master", type=MasterType, help="Switch master workspace"),
    arg('-s', "--slave", type=SlaveType),
    arg('-w', "--workspace", type=WorkspaceType),
    arg('-n', "--notify", action='store_true'),
]


def params_workspace(params):
    n_master, n_slave = get_workspace(params.master, params.slave, params.workspace)
    print(n_master, n_slave, params)
    if params.notify:
        osd.notify(workspace(n_master, n_slave), color="magenta", to='display', min_duration=0, duration=500)
    return n_master, n_slave


@main_function(["container-to", "c"], std_parser, "Move current workspace to specific output.")
def mf_container_to(params):
    n_master, n_slave = params_workspace(params)
    move_container(n_master, n_slave)


@main_function(["goto-with-container-to", "gc"], std_parser, "Move container to specified workspace and show it.")
def mf_goto_with_container_to(params):
    n_master, n_slave = params_workspace(params)
    move_container(n_master, n_slave)
    goto_workspace(n_master, n_slave)


@main_function(["goto-workspace", "g"], std_parser, "Show specific workspace.")
def mf_goto_workspace(params):
    n_master, n_slave = params_workspace(params)
    goto_workspace(n_master, n_slave)

@main_function(["gui"], [], "Show grafic user interface (only if you start daemon with `-g` option).")
def mf_gui(params):
    if shared.workspace_on[shared.output] == GUI_WORKSPACE:
        n_master, n_slave = get_workspace()
        goto_workspace(n_master, n_slave)
    else:
        goto_workspace(*GUI_WORKSPACE)


@main_function(["exit"], [], "Exit the daemon program.")
def mf_exit(params):
    os._exit(0)
