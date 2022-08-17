#!/usr/bin/env python3
import sys
import os
import osd

import argparse

import i3ipc

import signal

from i3_workspace_shared import *
from i3_workspace_lib import *
import i3_workspace_util as util
from i3_workspace_constants import *

def workspace(master, slave):
    if (master, slave) == GUI_WORKSPACE:
        return GUI_WORKSPACE_STR
    if slave > MAX_MASTERED_SLAVE:
        n = 900 + slave
    else:
        n = master * 10 + slave
    if n in WORKSPACES_RENAMES:
        return WORKSPACES_RENAMES[n]
    else:
        return str(n)


def parse_workspace(w_str):
    if w_str == GUI_WORKSPACE_STR:
        return GUI_WORKSPACE
    if w_str in REV_RENAMES:
        w = REV_RENAMES[w_str]
    else:
        try:
            w = int(w_str)
        except Exception:
            return None, None
    if w >= 1000 or w < 10:
        return None, None
    if w // 100 == 9:
        return (None, w % 100)
    else:
        return (w // 10, w % 10)


def goto_workspace(n_master, n_slave):
    master, slave = shared.workspace_on[shared.output]
    shared.qt_task("screenshot_and_goto", n_master, n_slave, master, slave) or shared.i3.value.command(f'workspace {workspace(n_master, n_slave)}')


def move_container(master, slave):
    shared.i3.value.command(f'move container to workspace {workspace(master, slave)}')
    shared.qt_task("ws_changed", master, slave)


def load_workspaces():
    i3_workspaces = shared.i3.value.get_workspaces()

    data = {parse_workspace(w.name): w.ipc_data['output'] for w in i3_workspaces}
    for w, output in data.items():
        event_workspace_is_on(w, output)
    for w in WORKSPACES:
        if w not in data:
            event_workspace_deleted(w)

    shared.outputs = {o.name: o for o in shared.i3.value.get_outputs()}


class WorkspaceOutOfRange(RuntimeError):
    pass


def get_workspace(master_cmd=None, slave_cmd=None, workspace_cmd=None, old_master=None, old_slave=None, gui=False):
    def master_next():
        nonlocal n_master
        nonlocal n_slave
        if gui:
            if n_slave is None:
                if n_master >= MAX_MASTER:
                    raise WorkspaceOutOfRange()
                else:
                    n_master += 1
            else:
                n_master = MIN_MASTER
                n_slave = None
        else:
            if n_slave is None:
                if n_master >= MAX_MASTER:
                    n_master = None
                    n_slave = MAX_MASTERED_SLAVE + 1
                else:
                    n_master += 1
                    n_slave = None
            else:
                if n_slave >= MAX_SLAVE:
                    raise WorkspaceOutOfRange()
                else:
                    n_slave += 1

    def master_prev():
        nonlocal n_master
        nonlocal n_slave
        if gui:
            if n_slave is None:
                if n_master <= MIN_MASTER:
                    n_slave = MAX_MASTERED_SLAVE + 2
                    n_master = None
                else:
                    n_master -= 1
            else:
                raise WorkspaceOutOfRange()
        else:
            if n_slave is None:
                if n_master <= MIN_MASTER:
                    raise WorkspaceOutOfRange()
                else:
                    n_master -= 1
                    n_slave = None
            else:
                if n_slave <= MAX_MASTERED_SLAVE + 1:
                    nmaster = MAX_MASTER
                    n_slave = None
                else:
                    n_slave -= 1

    def master_set(x):
        nonlocal n_master
        nonlocal n_slave
        n_master = x
        n_slave = None

    def master_alloc():
        nonlocal n_master
        nonlocal n_slave
        for i in range(MIN_MASTER, MAX_MASTER+1):
            if i not in shared.output_of_workspace:
                n_master = i
                n_slave = None
                return
        raise WorkspaceOutOfRange()

    def slave_change(by):
        nonlocal n_master
        nonlocal n_slave
        W = GUI_WORKSPACES_ORDER if gui else WORKSPACES
        W_REV = GUI_WORKSPACES_ORDER_REV if gui else WORKSPACES_REV
        try:
            ind = W_REV[(n_master if n_slave <= MAX_MASTERED_SLAVE else None, n_slave)] + by
            if ind < 0:
                raise WorkspaceOutOfRange()
            x_master, n_slave = W[ind]
            if x_master is not None:
                n_master = x_master
        except IndexError:
            raise WorkspaceOutOfRange()

    def slave_change_limit(by):
        nonlocal n_slave
        x = n_slave + by
        if x < MIN_SLAVE or x > MAX_SLAVE or (x <= MAX_MASTERED_SLAVE) != (n_slave <= MAX_MASTERED_SLAVE):
            raise WorkspaceOutOfRange()
        n_slave = x

    def slave_set(x):
        nonlocal n_master
        nonlocal n_slave
        n_slave = x

    def slave_alloc():
        nonlocal n_master
        nonlocal n_slave
        if n_master not in shared.output_of_workspace:
            n_slave = 1
            return
        for i in MASTERED_SLAVE_LIST:
            if i not in shared.output_of_workspace[n_master]:
                n_slave = i
                return
        raise WorkspaceOutOfRange()

    def rep_until_find(f, is_master=False):
        nonlocal n_master
        nonlocal n_slave

        x_master = None

        def go():
            nonlocal n_master
            nonlocal n_slave
            nonlocal x_master
            f()
            x_master = n_master if n_slave is None or n_slave <= MAX_MASTERED_SLAVE else None

        go()
        if is_master:
            if gui:
                while not x_master in shared.output_of_workspace:
                    go()
            else:
                while not (x_master in shared.output_of_workspace and (x_master is not None or n_slave in shared.output_of_workspace[x_master])):
                    go()
        else:
            while not (x_master in shared.output_of_workspace and n_slave in shared.output_of_workspace[x_master]):
                go()

    def proc_params(par, set_f, prev_f, next_f, alloc_f, prev_limit_f=None, next_limit_f=None, is_master=False):
        nonlocal n_master
        nonlocal n_slave
        if par is None:
            return
        if par == 'next-skip':
            rep_until_find(next_f, is_master)
        elif par == "next":
            next_f()
        elif par == 'prev-skip':
            rep_until_find(prev_f, is_master)
        elif par == "alloc":
            alloc_f()
        elif par == "prev":
            prev_f()
        elif par == 'next-limit-skip':
            rep_until_find(next_limit_f, is_master)
        elif par == "next-limit":
            next_limit_f()
        elif par == 'prev-limit-skip':
            rep_until_find(prev_limit_f, is_master)
        elif par == "prev-limit":
            prev_limit_f()
        else:
            set_f(int(par))

    n_master = shared.master_on[shared.output] if old_master is None else old_master

    if old_slave is None:
        n_slave = shared.slave_on[shared.output]
    else:
        n_slave = None if old_slave <= MAX_MASTERED_SLAVE else old_slave

    proc_params(master_cmd, master_set, master_prev, master_next, master_alloc, is_master=True)

    if n_slave is None:
        if n_master is not None and n_master == old_master:
            if old_slave <= MAX_MASTERED_SLAVE:
                n_slave = old_slave
    if n_slave is None:
        n_slave = shared.slave_on_for[shared.output][n_master]
    if n_slave is None:
        n_slave = shared.slave_for[n_master]
    if n_slave is None:
        for i in MASTERED_SLAVE_LIST:
            if n_master in shared.output_of_workspace and i in shared.output_of_workspace[n_master]:
                if shared.output_of_workspace[n_master][i] == shared.output:
                    n_slave = i
                    break
    if n_slave is None:
        for i in MASTERED_SLAVE_LIST:
            if n_master in shared.output_of_workspace and i in shared.output_of_workspace[n_master]:
                n_slave = i
                break
    if n_slave is None:
        n_slave = MASTERED_SLAVE_LIST[0]

    proc_params(slave_cmd, slave_set,
            lambda: slave_change(-1), lambda: slave_change(1),
            slave_alloc,
            lambda: slave_change_limit(-1), lambda: slave_change_limit(1),
    )

    if workspace_cmd is not None:
        n_master, n_slave = parse_workspace(workspace_cmd)
    if n_slave is None:
        raise RuntimeError("Workspace not parsed")
    return n_master, n_slave


from i3_workspace_watch import event_workspace_is_on, event_workspace_deleted
