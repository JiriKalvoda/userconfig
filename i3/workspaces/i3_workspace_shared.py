import sys
import os
import threading
from collections import defaultdict

import Xlib
import Xlib.display
import Xlib.X

import argparse

import i3ipc
from dataclasses import dataclass
import i3_workspace_util as util
from i3_workspace_constants import *


class Shared:
    output = None
    workspace_on = defaultdict(lambda: (None, None)) # could be GUI_WORKSPACE (the other data storage not)
    master_on = defaultdict(lambda: 1)
    slave_on = defaultdict(lambda: None)  # Only for non-mastered
    slave_for = defaultdict(lambda: None)
    slave_on_for = defaultdict(lambda: defaultdict(lambda: None))
    outputs = {}

    output_of_workspace = {}
    # indexed by [master][slave]
    # Unused workspaces are not in dict
    # Unused masters are too not in dict
    # master could be None

    qt_thread_tasker = None

    lock = util.AdvLock()

    i3 = threading.local()

    def qt_task(self, *arg, otherwise=lambda: False):
        # print(f"QT TASK FROM {threading.current_thread()}: {arg}")
        if self.qt_thread_tasker is None:
            return otherwise()
        with self.lock.pause_only_read_if_locked():
            self.qt_thread_tasker.f(*arg)

shared = Shared()
