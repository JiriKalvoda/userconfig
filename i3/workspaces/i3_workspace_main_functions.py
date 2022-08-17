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

main_functions = {}


def main_function(name):
    assert name not in main_functions

    def lam(f):
        main_functions[name] = f
        return f
    return lam


@main_function("reload")
def load(*a):
    load_workspaces()


@main_function("debug")
def debug_print(*a):
    print("output: ", output.output)
    print("master_on: ", output.master_on)
    print("slave_on: ", output.slave_on)
    print("slave_for: ", output.slave_for)
    print("slave_on_for: ", output.slave_on_for)
    print("output_of_workspace: ", output.output_of_workspace)




class ArgumentParserNoFail(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)



def parse_cmd(arg):
    parser = ArgumentParserNoFail(description='I3 workspace switcher')
    parser.add_argument('-m', "--master", type=str, help="Switch master workspace")
    parser.add_argument('-s', "--slave", type=str)
    parser.add_argument('-w', "--workspace", type=str)
    parser.add_argument('-n', "--notify", action='store_true')
    params = parser.parse_args(arg[1:])

    n_master, n_slave = get_workspace(params.master, params.slave, params.workspace)
    print(n_master, n_slave, params)
    if params.notify:
        osd.notify(workspace(n_master, n_slave), color="magenta", to='display', min_duration=0, duration=500)
    return n_master, n_slave, params


@main_function("container-to")
@main_function("c")
def mf_container_to(arg):
    n_master, n_slave, params = parse_cmd(arg)
    move_container(n_master, n_slave)


@main_function("goto-with-container-to")
@main_function("gc")
def mf_goto_with_container_to(arg):
    n_master, n_slave, params = parse_cmd(arg)
    move_container(n_master, n_slave)
    goto_workspace(n_master, n_slave)


@main_function("goto-workspace")
@main_function("g")
def mf_goto_workspace(arg):
    n_master, n_slave, params = parse_cmd(arg)
    goto_workspace(n_master, n_slave)

@main_function("gui")
def mf_gui(arg):
    if shared.workspace_on[shared.output] == GUI_WORKSPACE:
        n_master, n_slave = get_workspace()
        goto_workspace(n_master, n_slave)
    else:
        goto_workspace(*GUI_WORKSPACE)


@main_function("exit")
def mf_exit(arg):
    os._exit(0)
