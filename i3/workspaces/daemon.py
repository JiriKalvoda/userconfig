#!/usr/bin/env python3
import sys
import os
import threading
from collections import defaultdict

import Xlib
import Xlib.display
import Xlib.X

import argparse

import i3ipc
import time
import traceback

lock = threading.Lock()

ATOP_PREFIX = "WS_"

def defautl_val(*ar):
    for i in ar:
        if i is not None:
            return i
    return None


i3 = i3ipc.Connection()



display = Xlib.display.Display()
root_win = display.screen().root


root_win.change_attributes(event_mask=Xlib.X.PropertyChangeMask)


# root_win.delete_property(queue_atom)


def get_queue():
    queue_atom = display.get_atom(ATOP_PREFIX + "QUEUE")
    while True:
        e = display.next_event()
        if e.type == Xlib.X.PropertyNotify:
            #print(e, e.state, e.window, e.atom)
            if( e.state == Xlib.X.PropertyNewValue
                and e.window == root_win
                and e.atom == queue_atom):
                # print("Z")
                x = root_win.get_property(queue_atom, Xlib.Xatom.STRING, 0, 1, delete=1)
                # print(x)
                msg = x.value
                # print("=>", msg, x.bytes_after, type(x.bytes_after))
                while x.bytes_after > 0:
                    x = root_win.get_property(queue_atom, Xlib.Xatom.STRING, len(msg) // 4, 1, delete=1)
                    # print(x)
                    msg += x.value
                    # print("=>", msg, x.bytes_after)
                display.flush()
                yield from map(lambda x: x[1:].split('\n>'), msg.decode().split('\n\n')[:-1])
                # print(x.value.decode())

main_functions = {}


def main_function(name):
    assert name not in main_functions

    def lam(f):
        main_functions[name] = f
        return f
    return lam

######################################
######################################
######################################


MAX_MASTERED_SLAVE = 8


output = None
master_on = defaultdict(lambda: 1)
slave_on = defaultdict(lambda: None)  # Only for non-mastered
slave_for = defaultdict(lambda: 1)
slave_on_for = defaultdict(lambda: defaultdict(lambda: None))


@main_function("debug")
def debug_print(*a):
    print("output: ", output)
    print("master_on: ", master_on)
    print("slave_on: ", slave_on)
    print("slave_for: ", slave_for)
    print("slave_on_for: ", slave_on_for)

workspaces_renames = {9913: "MAIL", 9914: "ZOOM"}

rev_renames = {v: k for (k, v) in workspaces_renames.items()}


def workspace(master, slave):
    if slave > MAX_MASTERED_SLAVE:
        n = 9900 + slave
    else:
        n = master * 100 + slave
    if n in workspaces_renames:
        return workspaces_renames[n]
    else:
        return str(n)


def parse_workspace(w_str):
    if w_str in rev_renames:
        w = rev_renames[w_str]
    else:
        try:
            w = int(w_str)
        except Exception:
            return None, None
    if w >= 10000 or w < 100:
        return None, None
    if w // 100 == 99:
        return (None, w % 100)
    else:
        return (w // 100, w % 100)


def goto_workspace(n_master, n_slave):
    i3.command(f'workspace {workspace(n_master, n_slave)}')


def move_container(master, slave):
    i3.command(f'move container to workspace {workspace(master, slave)}')



def parse_m_s(arg):
    parser = argparse.ArgumentParser(description='I3 workspace switcher')
    parser.add_argument('-m', "--master", type=int, help="Switch master workspace")
    parser.add_argument('-s', "--slave", type=int)
    parser.add_argument('-w', "--workspace", type=str)
    params = parser.parse_args(arg[1:])
    n_master = master_on[output]
    if params.master is not None:
        n_master = int(params.master)
    n_slave = slave_on_for[output][n_master]
    if n_slave is None:
        n_slave = slave_for[n_master]
    if params.slave is not None:
        n_slave = int(params.slave)
    if params.workspace is not None:
        n_master, n_slave = parse_workspace(params.workspace)
    if n_slave is None:
        raise RuntimeError("Workspace not parsed")
    print(n_master, n_slave, params)
    return n_master, n_slave


@main_function("container-to")
@main_function("c")
def mf_container_to(arg):
    n_master, n_slave = parse_m_s(arg)
    move_container(n_master, n_slave)


@main_function("goto-with-container-to")
@main_function("gc")
def mf_goto_with_container_to(arg):
    n_master, n_slave = parse_m_s(arg)
    move_container(n_master, n_slave)
    goto_workspace(n_master, n_slave)


@main_function("goto-workspace")
@main_function("g")
def mf_goto_workspace(arg):
    n_master, n_slave = parse_m_s(arg)
    goto_workspace(n_master, n_slave)


@main_function("exit")
def mf_exit(arg):
    os._exit(0)


goto_workspace(1, 1)


######################################
######################################
######################################


def i3_watch():
    i3ipcs = i3ipc
    i3s = i3ipc.Connection()

    def on_workspace_focus(i3, e):
        with lock:
            global output
            output = e.current.ipc_data['output']
            master, slave = parse_workspace(e.current.name)
            print(master, slave)
            if slave is not None:
                if master:
                    master_on[output] = master
                    slave_for[master] = slave
                    slave_on_for[output][master] = slave
                    slave_on[output] = None
                else:
                    slave_on[output] = slave

    def on_workspace_removed(i3, e):
        with lock:
            master, slave = parse_workspace(e.current.name)
            if slave is not None:
                if master is None:
                    for k in slave_on:
                        if slave_on[k] == slave:
                            slave_on[k] = None
                else:
                    for k in slave_on_for:
                        if slave_on_for[k][master] == slave:
                            slave_on_for[k][master] = None
                    if slave_for[master] == slave:
                        slave_for[master] = 1
            print(f'############### workspace just got removed: {e.current.name}')


    def on_workspace_moved(i3, e):
        with lock:
            master, slave = parse_workspace(e.current.name)
            n_output = e.current.ipc_data['output']
            if slave is not None:
                if master is None:
                    for k in slave_on:
                        if slave_on[k] == slave and k != n_output:
                            slave_on[k] = None
                else:
                    for k in slave_on_for:
                        if slave_on_for[k][master] == slave and k != n_output:
                            slave_on_for[k][master] = None
            if slave is not None:
                if master:
                    pass
                else:
                    pass
            print(f'############### workspace just got moved: {e.current.name} {e}')


    i3s.on(i3ipc.Event.WORKSPACE_FOCUS, on_workspace_focus)
    i3s.on(i3ipc.Event.WORKSPACE_EMPTY, on_workspace_removed)
    i3s.on(i3ipc.Event.WORKSPACE_MOVE, on_workspace_moved)

    i3s.main()


i3_watch_thread = threading.Thread(target=i3_watch)
i3_watch_thread.setDaemon(True)
i3_watch_thread.start()

######################################
######################################
######################################


for msg in get_queue():
    print(msg)
    if len(msg) >= 1:
        try:
            with lock:
                main_functions[msg[0]](msg)
        except Exception as e:
            traceback.print_exc()
