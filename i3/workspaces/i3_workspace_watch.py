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
from i3_workspace_lib import workspace, parse_workspace, load_workspaces
import i3_workspace_util as util
from i3_workspace_constants import *


def event_workspace_is_on(w, output):
    master, slave = w
    if slave is not None:
        shared.output_of_workspace.setdefault(master, {})
        shared.output_of_workspace[master][slave] = output
        shared.qt_task("ws_exist", master, slave)
        shared.qt_task("ws_metadata_changed", master, slave)


def event_workspace_deleted(w):
    master, slave = w
    if slave is not None:
        if master is None:
            for k in shared.slave_on:
                if shared.slave_on[k] == slave:
                    shared.slave_on[k] = None
        else:
            for k in shared.slave_on_for:
                if shared.slave_on_for[k][master] == slave:
                    shared.slave_on_for[k][master] = None
            if shared.slave_for[master] == slave:
                shared.slave_for[master] = None
        shared.qt_task("ws_removed", master, slave)
        shared.qt_task("ws_metadata_changed", master, slave)
    if master in shared.output_of_workspace:
        if slave in shared.output_of_workspace[master]:
            shared.output_of_workspace[master].pop(slave)
        if shared.output_of_workspace[master] == {}:
            shared.output_of_workspace.pop(master)


def i3_watch():
    shared.i3.value = i3ipc.Connection()

    def on_workspace_focus(i3p, e):
        with shared.lock:
            output = e.current.ipc_data['output']
            if output != shared.output:
                shared.qt_task("screenshot", *shared.workspace_on[shared.output])
            shared.output = output
            master, slave = parse_workspace(e.current.name)
            event_workspace_is_on((master, slave), shared.output)
            shared.qt_task("ws_metadata_changed", *shared.workspace_on[shared.output])
            shared.workspace_on[shared.output] = (master, slave)
            shared.qt_task("ws_changed", master, slave)
            if (master, slave) == GUI_WORKSPACE:
                shared.qt_task("gui_focused")
            else:
                if slave is not None:
                    if master:
                        shared.qt_task("ws_metadata_changed", master, shared.slave_for[master])
                        shared.qt_task("ws_metadata_changed", master, shared.slave_on_for[shared.output][master])
                        shared.master_on[shared.output] = master
                        shared.slave_for[master] = slave
                        shared.slave_on_for[shared.output][master] = slave
                        shared.slave_on[shared.output] = None
                    else:
                        shared.slave_on[shared.output] = slave
                shared.qt_task("ws_metadata_changed", master, slave)

    def on_workspace_removed(i3p, e):
        with shared.lock:
            event_workspace_deleted(parse_workspace(e.current.name))


    def on_workspace_moved(i3p, e):
        with shared.lock:
            master, slave = parse_workspace(e.current.name)
            n_output = e.current.ipc_data['output']
            event_workspace_is_on((master, slave), n_output)
            if slave is not None:
                if master is None:
                    for k in shared.slave_on:
                        if shared.slave_on[k] == slave and k != n_output:
                            shared.slave_on[k] = None
                else:
                    for k in shared.slave_on_for:
                        if shared.slave_on_for[k][master] == slave and k != n_output:
                            shared.slave_on_for[k][master] = None
                shared.qt_task("ws_metadata_changed", master, slave)

    def on_workspace_created(i3, e):
        with shared.lock:
            master, slave = parse_workspace(e.current.name)
            n_output = e.current.ipc_data['output']
            shared.output_of_workspace.setdefault(master, {})
            shared.output_of_workspace[master][slave] = n_output

    def on_output_changed(i3, e):
        with shared.lock:
            load_workspaces()

    shared.i3.value.on(i3ipc.Event.WORKSPACE_FOCUS, on_workspace_focus)
    shared.i3.value.on(i3ipc.Event.WORKSPACE_EMPTY, on_workspace_removed)
    shared.i3.value.on(i3ipc.Event.WORKSPACE_MOVE, on_workspace_moved)
    shared.i3.value.on(i3ipc.Event.WORKSPACE_INIT, on_workspace_created)
    shared.i3.value.on(i3ipc.Event.OUTPUT, on_output_changed)

    shared.i3.value.main()
