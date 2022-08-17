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
from i3_workspace_main_functions import main_functions
from i3_workspace_constants import *



parser = argparse.ArgumentParser(description='I3 workspace switcher')
parser.add_argument('-g', "--gui", action='store_true')
# parser.add_argument('-d' , "--debug-qt-task", action='store_true')
params = parser.parse_args()

USE_QT = params.gui
# DEBUG_QT_TASK = params.debug_qt_task

display = Xlib.display.Display()
root_win = display.screen().root

root_win.change_attributes(event_mask=Xlib.X.PropertyChangeMask)

osd.default_connection = osd.Connection(display)


def get_queue():
    queue_atom = display.get_atom("WS_QUEUE")
    root_win.delete_property(queue_atom)
    while True:
        e = display.next_event()
        if e.type == Xlib.X.PropertyNotify:
            if( e.state == Xlib.X.PropertyNewValue
                and e.window == root_win
                and e.atom == queue_atom):
                x = root_win.get_property(queue_atom, Xlib.Xatom.STRING, 0, 1, delete=1)
                if x is None:
                    continue
                msg = x.value
                while x.bytes_after > 0:
                    x = root_win.get_property(queue_atom, Xlib.Xatom.STRING, len(msg) // 4, 1, delete=1)
                    if x is None:
                        break
                    msg += x.value
                display.flush()
                yield from map(lambda x: x[1:].split('\n>'), msg.decode().split('\n\n')[:-1])


def x_main():
    shared.i3.value = i3ipc.Connection()

    load_workspaces()

    goto_workspace(1, 1)

    for msg in get_queue():
        print(msg)
        if len(msg) >= 1:
            try:
                with shared.lock:
                    main_functions[msg[0]](msg)
            except WorkspaceOutOfRange:
                osd.notify("No more workspaces", color="magenta", to='display', min_duration=0)
            except Exception as e:
                traceback.print_exc()

i3_watch_thread = threading.Thread(target=i3_watch)
i3_watch_thread.daemon = True
i3_watch_thread.start()

if USE_QT:
    from i3_workspace_qt import qt_main
    x_thread = threading.Thread(target=x_main)
    x_thread.daemon = True
    x_thread.start()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    qt_main()
else:
    x_main()
