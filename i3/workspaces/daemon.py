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

parser = argparse.ArgumentParser(description='I3 workspace switcher')
parser.add_argument('-q', "--qt", action='store_true')
parser.add_argument('-d' , "--debug-qt-task", action='store_true')
params = parser.parse_args()

USE_QT = params.qt
DEBUG_QT_TASK = params.debug_qt_task

if USE_QT:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    import regex

    qtoverride = lambda x: x  # only documentation of code

    class FlowLayout(QLayout):
        # Taken from https://doc.qt.io/qtforpython/examples/example_widgets_layouts_flowlayout.html
        # Modificated
        def __init__(self, parent=None):
            super().__init__(parent)

            if parent is not None:
                self.setContentsMargins(QMargins(0, 0, 0, 0))

            self._item_list = []

        def __del__(self):
            item = self.takeAt(0)
            while item:
                item = self.takeAt(0)

        @qtoverride
        def addItem(self, item):
            self._item_list.append(item)

        @qtoverride
        def count(self):
            return len(self._item_list)

        @qtoverride
        def itemAt(self, index):
            if 0 <= index < len(self._item_list):
                return self._item_list[index]

            return None

        @qtoverride
        def takeAt(self, index):
            if 0 <= index < len(self._item_list):
                return self._item_list.pop(index)

            return None

        @qtoverride
        def expandingDirections(self):
            return Qt.Orientation(0)

        @qtoverride
        def hasHeightForWidth(self):
            return True

        @qtoverride
        def heightForWidth(self, width):
            height = self._do_layout(QRect(0, 0, width, 0), True)
            return height

        @qtoverride
        def setGeometry(self, rect):
            super(FlowLayout, self).setGeometry(rect)
            self._do_layout(rect, False)

        @qtoverride
        def sizeHint(self):
            return self.minimumSize()

        @qtoverride
        def minimumSize(self):
            size = QSize()

            for item in self._item_list:
                size = size.expandedTo(item.minimumSize())

            size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
            return size

        def _do_layout(self, rect, test_only):
            @dataclass
            class Member:
                widget: QWidget
                x: int
                y: int
                width: int
                height: int

                def set_geometry(self):
                    self.widget.setGeometry(QRect(QPoint(self.x, self.y), QSize(self.width, self.height)))

            members = [[]]

            x = rect.x()
            y = rect.y()
            line_height = 0
            spacing = self.spacing()

            for item in self._item_list:
                hint = item.sizeHint()
                style = item.widget().style()
                layout_spacing_x = style.layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal
                )
                layout_spacing_y = style.layoutSpacing(
                    QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical
                )
                space_x = 0
                space_y = 0
                next_x = x + hint.width() + space_x
                if next_x - space_x > rect.right() and line_height > 0:
                    x = rect.x()
                    y = y + line_height + space_y
                    next_x = x + hint.width() + space_x
                    line_height = 0
                    members.append([])

                members[-1].append(Member(item, x, y, hint.width(), hint.height()))
                x = next_x
                line_height = max(line_height, item.sizeHint().height())

            for i in members:
                h = max([j.height for j in i])
                w = sum([j.width for j in i])
                max_w = sum([j.widget.maximumSize().width() for j in i])
                could_add = max_w - w
                to_add = min(could_add, rect.width()-w)
                add_x = 0
                for j in i:
                    j.height = h
                    j.x += add_x
                    if could_add:
                        this_could_add = j.widget.maximumSize().width() - j.width
                        add = to_add * this_could_add // could_add
                        to_add -= add
                        could_add -= this_could_add
                        j.width += add
                        add_x += add

            if not test_only:
                for i in members:
                    for j in i:
                        j.set_geometry()
            return y + line_height - rect.y()

    class QNoArrowScrollArea(QScrollArea):
        def __init__(self, parent=None):
            super().__init__(parent)

        @qtoverride
        def keyPressEvent(self, event):
            if event.key() in {Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down}:
                event.ignore()
            else:
                super().keyPressEvent(event)


class NoneContext:
    def __enter__(self):
        pass
    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

def iford(x):
    return x if type(x) is int else ord(x)

class AdvLock:
    write_lock = threading.Lock()
    write_thrad = None
    read_lock = threading.Lock()

    def __enter__(self):
        self.write_lock.acquire()
        self.write_thrad = threading.current_thread()
        self.read_lock.acquire()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.read_lock.release()
        self.write_thrad = None
        self.write_lock.release()

    def __init__(self):
        class Read:
            def __enter__(s):
                self.read_lock.acquire()
            def __exit__(s, exc_type, exc_value, exc_traceback):
                self.read_lock.release()
        self.read = Read()

        class PauseOnlyRead:
            def __enter__(s):
                self.read_lock.release()
            def __exit__(s, exc_type, exc_value, exc_traceback):
                self.read_lock.acquire()
        self.pause_only_read = PauseOnlyRead()

    def pause_only_read_if_locked(self):
        if self.write_thrad == threading.current_thread():
            return self.pause_only_read
        return NoneContext



lock = AdvLock()

def defautl_val(*ar):
    for i in ar:
        if i is not None:
            return i
    return None


i3 = threading.local()



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

GUI_WORKSPACE = (-1, -1)
GUI_WORKSPACE_STR = "0"

MAX_MASTERED_SLAVE = 8
MAX_SLAVE = 14
MAX_MASTER = 12
MIN_SLAVE = 0
MIN_MASTER = 1
MASTERED_SLAVE_LIST = list(range(1, MAX_MASTERED_SLAVE+1)) + [0]

WORKSPACES_RENAMES = {913: "MAIL", 914: "ZOOM"}
REV_RENAMES = {v: k for (k, v) in WORKSPACES_RENAMES.items()}
WORKSPACES_KEY = {911: "-", 912: "=", 913: "M", 914: "Z"}
ORD_TO_WORKSPACE = {iford(v): k for k, v in WORKSPACES_KEY.items()}


def run(*arg, **kvarg):
    return lambda f: f(*arg, *kvarg)

@list
@run()
def WORKSPACES():
    for i in range(MIN_MASTER, MAX_MASTER + 1):
        for j in range(MIN_SLAVE, MAX_MASTERED_SLAVE + 1):
            yield (i, j)
    for j in range(MAX_MASTERED_SLAVE + 1, MAX_SLAVE + 1):
        yield (None, j)


WORKSPACES_REV = {x: i for (i, x) in enumerate(WORKSPACES)}

GUI_MASTERS = [None] + list(range(MIN_MASTER, MAX_MASTER+1))
GUI_WORKSPACES_ORDER = [i for i in WORKSPACES if i[0] is None] + [i for i in WORKSPACES if i[0] is not None]


GUI_WORKSPACES_ORDER_REV = {x: i for (i, x) in enumerate(GUI_WORKSPACES_ORDER)}

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

def qt_task(*arg, otherwise=lambda: False):
    if DEBUG_QT_TASK:
        print(f"QT TASK FROM {threading.current_thread()}: {arg}")
    if qt_thread_tasker is None:
        return otherwise()
    with lock.pause_only_read_if_locked():
        qt_thread_tasker.f(*arg)
    if DEBUG_QT_TASK:
        print(f"QT TASK END")



@main_function("reload")
def load(*a):
    i3_workspaces = i3.value.get_workspaces()

    data = {parse_workspace(w.name): w.ipc_data['output'] for w in i3_workspaces}
    for w, output in data.items():
        event_workspace_is_on(w, output)
    for w in WORKSPACES:
        if w not in data:
            event_workspace_deleted(w)

    global outputs
    outputs = {o.name: o for o in i3.value.get_outputs()}


@main_function("debug")
def debug_print(*a):
    print("output: ", output)
    print("master_on: ", master_on)
    print("slave_on: ", slave_on)
    print("slave_for: ", slave_for)
    print("slave_on_for: ", slave_on_for)
    print("output_of_workspace: ", output_of_workspace)



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
    master, slave = workspace_on[output]
    qt_task("screenshot_and_goto", n_master, n_slave, master, slave) or  i3.value.command(f'workspace {workspace(n_master, n_slave)}')


def move_container(master, slave):
    i3.value.command(f'move container to workspace {workspace(master, slave)}')
    qt_task("ws_changed", master, slave)


class ArgumentParserNoFail(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


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
            if i not in output_of_workspace:
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
        if n_master not in output_of_workspace:
            n_slave = 1
            return
        for i in MASTERED_SLAVE_LIST:
            if i not in output_of_workspace[n_master]:
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
                while not x_master in output_of_workspace:
                    go()
            else:
                while not (x_master in output_of_workspace and (x_master is not None or n_slave in output_of_workspace[x_master])):
                    go()
        else:
            while not (x_master in output_of_workspace and n_slave in output_of_workspace[x_master]):
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

    n_master = master_on[output] if old_master is None else old_master

    if old_slave is None:
        n_slave = slave_on[output]
    else:
        n_slave = None if old_slave <= MAX_MASTERED_SLAVE else old_slave

    proc_params(master_cmd, master_set, master_prev, master_next, master_alloc, is_master=True)

    if n_slave is None:
        if n_master is not None and n_master == old_master:
            if old_slave <= MAX_MASTERED_SLAVE:
                n_slave = old_slave
    if n_slave is None:
        n_slave = slave_on_for[output][n_master]
    if n_slave is None:
        n_slave = slave_for[n_master]
    if n_slave is None:
        for i in MASTERED_SLAVE_LIST:
            if n_master in output_of_workspace and i in output_of_workspace[n_master]:
                if output_of_workspace[n_master][i] == output:
                    n_slave = i
                    break
    if n_slave is None:
        for i in MASTERED_SLAVE_LIST:
            if n_master in output_of_workspace and i in output_of_workspace[n_master]:
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
    if workspace_on[output] == GUI_WORKSPACE:
        n_master, n_slave = get_workspace()
        goto_workspace(n_master, n_slave)
    else:
        goto_workspace(*GUI_WORKSPACE)


@main_function("exit")
def mf_exit(arg):
    os._exit(0)




######################################
######################################
######################################

def event_workspace_is_on(w, output):
    master, slave = w
    if slave is not None:
        output_of_workspace.setdefault(master, {})
        output_of_workspace[master][slave] = output
        qt_task("ws_exist", master, slave)
        qt_task("ws_metadata_changed", master, slave)


def event_workspace_deleted(w):
    master, slave = w
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
                slave_for[master] = None
        qt_task("ws_removed", master, slave)
        qt_task("ws_metadata_changed", master, slave)
    if master in output_of_workspace:
        if slave in output_of_workspace[master]:
            output_of_workspace[master].pop(slave)
        if output_of_workspace[master] == {}:
            output_of_workspace.pop(master)


def i3_watch():
    i3.value = i3ipc.Connection()

    def on_workspace_focus(i3p, e):
        with lock:
            global output
            output = e.current.ipc_data['output']
            master, slave = parse_workspace(e.current.name)
            event_workspace_is_on((master, slave), output)
            qt_task("ws_metadata_changed", *workspace_on[output])
            workspace_on[output] = (master, slave)
            qt_task("ws_changed", master, slave)
            if (master, slave) == GUI_WORKSPACE:
                qt_task("gui_focused")
            else:
                print(master, slave)
                if slave is not None:
                    if master:
                        qt_task("ws_metadata_changed", master, slave_for[master])
                        qt_task("ws_metadata_changed", master, slave_on_for[output][master])
                        master_on[output] = master
                        slave_for[master] = slave
                        slave_on_for[output][master] = slave
                        slave_on[output] = None
                    else:
                        slave_on[output] = slave
                qt_task("ws_metadata_changed", master, slave)

    def on_workspace_removed(i3p, e):
        with lock:
            event_workspace_deleted(parse_workspace(e.current.name))


            print(f'############### workspace just got removed: {e.current.name}')


    def on_workspace_moved(i3p, e):
        with lock:
            master, slave = parse_workspace(e.current.name)
            n_output = e.current.ipc_data['output']
            event_workspace_is_on((master, slave), n_output)
            if slave is not None:
                if master is None:
                    for k in slave_on:
                        if slave_on[k] == slave and k != n_output:
                            slave_on[k] = None
                else:
                    for k in slave_on_for:
                        if slave_on_for[k][master] == slave and k != n_output:
                            slave_on_for[k][master] = None
                qt_task("ws_metadata_changed", master, slave)
            print(f'############### workspace just got moved: {e.current.name} {e}')

    def on_workspace_created(i3, e):
        with lock:
            master, slave = parse_workspace(e.current.name)
            n_output = e.current.ipc_data['output']
            output_of_workspace.setdefault(master, {})
            output_of_workspace[master][slave] = n_output

    def on_output_changed(i3, e):
        with lock:
            load()

    i3.value.on(i3ipc.Event.WORKSPACE_FOCUS, on_workspace_focus)
    i3.value.on(i3ipc.Event.WORKSPACE_EMPTY, on_workspace_removed)
    i3.value.on(i3ipc.Event.WORKSPACE_MOVE, on_workspace_moved)
    i3.value.on(i3ipc.Event.WORKSPACE_INIT, on_workspace_created)
    i3.value.on(i3ipc.Event.OUTPUT, on_output_changed)

    i3.value.main()


######################################
######################################
######################################


def qt_main():


    i3.value = i3ipc.Connection()
    app = QApplication(sys.argv)

    s = app.primaryScreen()

    def no_space(lay):
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        return lay

    def qt_workspace_widget_func(master, slave, f):
        if slave is None or (slave, master) == GUI_WORKSPACE:
            return
        if slave > MAX_MASTERED_SLAVE:
            master = None
        return f(m_win.workspaces[(master, slave)])

    SCREENSHOTS_SIZES = [120, 150, 200, 250, 300, 400, 500, 750, 1000]

    # An object containing methods you want to run in a thread
    class Tasker(QObject):
        do = pyqtSignal(object)
        func = {}

        def f(self, *arg):
            self.do.emit(arg)

        @pyqtSlot(object)
        def _run(self, w):
            if DEBUG_QT_TASK:
                    print(f"QT TASK SLOT {threading.current_thread()}: {w}")
            try:
                self.func[w[0]](*w[1:])
            except Exception:
                traceback.print_exc()

        def __init__(self, parent = None):
            super().__init__(parent)
            self.do.connect(self._run)

            def func_add(f):
                self.func[f.__name__] = f
                return f

            @func_add
            def ws_removed(master, slave):
                qt_workspace_widget_func(master, slave, lambda x: x.removed())

            @func_add
            def ws_changed(master, slave):
                qt_workspace_widget_func(master, slave, lambda x: x.screenshot_changed())

            @func_add
            def ws_exist(master, slave):
                qt_workspace_widget_func(master, slave, lambda x: x.make_exist())

            @func_add
            def ws_metadata_changed(master, slave):
                qt_workspace_widget_func(master, slave, lambda x: x.metadata_changed())

            @func_add
            def screenshot_and_goto(n_master, n_slave, master, slave):
                qt_workspace_widget_func(master, slave, lambda x: x.make_screenshot())
                i3.value.command(f'workspace {workspace(n_master, n_slave)}')

            @func_add
            def gui_focused():
                m_win.load_i3_tree()
                with lock.read:
                    w = get_workspace()
                m_win.focus_workspace(*w)

    global qt_thread_tasker
    qt_thread_tasker = Tasker()

    class I3WindowNodeWidget(QLabel):
        def __init__(self, t, parent=None):
            super().__init__(parent)
            self.title = t.name
            self.setText(self.title)
            self.setAutoFillBackground(True)


    class I3InnerNodeWidget(QWidget):
        def __init__(self, t, parent=None):
            super().__init__(parent)
            self.hlay = no_space(QHBoxLayout(self))
            self.head = QLabel(self)
            self.list = QWidget(self)
            self.list_lay = no_space(QVBoxLayout(self.list))

            self.list.setLayout(self.list_lay)
            self.setLayout(self.hlay)
            self.hlay.addWidget(self.head)
            self.hlay.addWidget(self.list)

            self.head.setText({
                "splith": "H",
                "splitv": "V",
                "tabbed": "T",
                "stacked": "S"
            }.get(t.layout, "?"))
            self.head.setFixedWidth(13)

            self.nodes = [i3_tree_widget_create(i, self) for i in  t.nodes]
            for i in self.nodes:
                self.list_lay.addWidget(i)

    def i3_tree_widget_create(t, parent):
        if t.nodes:
            return I3InnerNodeWidget(t, parent)
        else:
            return I3WindowNodeWidget(t, parent)

    class I3TreeWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.lay = no_space(QVBoxLayout(self))
            self.setLayout(self.lay)
            self.all_inner_nides = []
            self.all_window_nodes = []
            self.find_matchs = []

        def clear(self):
            while (i := self.lay.takeAt(0)):
                i.widget().hide()
            self.all_inner_nides = []
            self.all_window_nodes = []
            self.find_matchs = []

        def set_tree(self, t):
            self.clear()
            def go(x):
                if isinstance(x, I3WindowNodeWidget):
                    self.all_window_nodes.append(x)
                if isinstance(x, I3InnerNodeWidget):
                    self.all_inner_nides.append(x)
                    for i in x.nodes:
                        go(i)
            r = i3_tree_widget_create(t, self)
            go(r)
            self.lay.addWidget(r)
            for i in t.floating_nodes:
                for j in i.nodes:
                    f = i3_tree_widget_create(j, self)
                    go(f)
                    self.lay.addWidget(f)

        def find(self, r):
            for win in self.all_window_nodes:
                m = r.search(win.title, partial=False)
                if m:
                    span = m.span()

                    t = win.title
                    win.setText(t[:span[0]] + "<b>" + t[span[0]:span[1]] + "</b>" + t[span[1]:])
                    p = QPalette()
                    p.setColor(win.backgroundRole(), QColor(255,255,0))
                    win.setPalette(p)
                    self.find_matchs.append((win, m))

        def clear_find(self):
            for win,m in self.find_matchs:
                p = QPalette()
                p.setColor(win.backgroundRole(), QColor(0,0,0,0))
                win.setPalette(p)
                win.setText(win.title)
            self.find_matchs = []



    class WorkspaceWidget(QFrame):
        screenshot = None
        screenshot_is_old = False
        exist = False

        def __init__(self, master, slave, parent):
            self.m_win = parent
            super().__init__(parent)
            self.setFrameShape(QFrame.Box)
            self.master = master
            self.slave = slave
            self.lay = no_space(QVBoxLayout(self))
            self.l_name = QLabel(self)
            self.l_screenshot = QLabel(self)
            self.l_tree = I3TreeWidget(self)


            self.lay.addWidget(self.l_name)
            self.lay.addWidget(self.l_screenshot)
            self.lay.addWidget(self.l_tree)
            self.lay.addStretch()
            self.setLayout(self.lay)
            self.l_name.setAlignment(Qt.AlignCenter)


            self.metadata_changed()

        @qtoverride
        def mousePressEvent(self, event):
            print(event, type(event), event.pos(), int(event.flags()), event.buttons())
            event.accept()
            i3.value.command(f'workspace {workspace(self.master, self.slave)}')

        def redraw_pic(self):
            w = self.m_win.screenshot_size
            self.setMaximumSize(w,2*w+1000)
            if self.exist:
                if self.screenshot:
                    s = self.screenshot.scaled(w, 2*w, Qt.KeepAspectRatio)
                else:
                    s = QPixmap(w, w*9//16)
                    s.fill(QColor(0,0,0))
                if self.screenshot_is_old or not self.screenshot:
                    painter = QPainter(s)
                    red = QPen(QColor(255, 0, 0), 5)
                    painter.setPen(red)
                    painter.drawLine(0, 0, s.width(), s.height())
                    painter.drawLine(0, s.height(), s.width(), 0)
                    painter.end()
                self.l_screenshot.setPixmap(s)
                self.l_screenshot.setScaledContents(False)
            else:
                self.l_screenshot.clear()


        def make_screenshot(self):
            self.exist = True
            with lock.read:
                try:
                    o = output_of_workspace[self.master][self.slave]
                    rect = outputs[o].rect
                except KeyError:
                    return
            self.screenshot = s.grabWindow(QApplication.desktop().winId(), rect.x, rect.y, rect.x+rect.width, rect.y+rect.height)
            self.screenshot_is_old = False
            self.redraw_pic()

        def screenshot_changed(self):
            self.screenshot_is_old = True
            self.exist = True
            self.redraw_pic()

        def make_exist(self):
            self.exist = True
            self.redraw_pic()

        def removed(self):
            self.screenshot = None
            self.exist = False
            self.redraw_pic()
            self.l_tree.clear()

        def metadata_changed(self):
            self.l_name.setText(f"<b>{workspace(self.master, self.slave)}")
            p_name = QPalette()
            p_name.setColor(QPalette.WindowText, QColor(0,0,0))

            self.l_name.setAutoFillBackground(True)
            with lock.read:
                try:
                    if outputs[output_of_workspace[self.master][self.slave]].primary:
                        p_name.setColor(QPalette.Window, QColor(255, 255, 255))
                    else:
                        p_name.setColor(QPalette.Window, QColor(180, 180, 180))
                except KeyError:
                    pass
                if (self.master, self.slave) in workspace_on.values():
                        p_name.setColor(QPalette.WindowText, QColor(0,255,0))
                elif self.master is not None:
                    if slave_for[self.master] == self.slave:
                        p_name.setColor(QPalette.WindowText, QColor(255,0,0))
                    else:
                        for x in slave_on_for.values():
                            if x is not None and x[self.master] == self.slave:
                                p_name.setColor(QPalette.WindowText, QColor(0,0,255))
                                break

            self.l_name.setPalette(p_name)

        def parse_i3_tree(self, t):
            s = ""
            print(s)
            self.l_tree.set_tree(t)

        def setColor(self, color):
            pal = self.palette()
            pal.setColor(QPalette.WindowText, color)
            self.setPalette(pal)



    class MainWindow(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.screenshot_size = 300

            self.lay = no_space(QVBoxLayout(self))
            self.lay.setContentsMargins(0, 0, 0, 0)
            self.scroll = QNoArrowScrollArea(self)
            self.scroll_widget = QWidget(self)
            self.scroll_lay = no_space(QVBoxLayout(self.scroll_widget))
            self.master_widget = {i: QWidget(self) for i in GUI_MASTERS}
            self.master_lay = {i: FlowLayout(self.master_widget[i]) for i in GUI_MASTERS}
            self.workspaces = {(master,slave): WorkspaceWidget(master, slave, self) for (master, slave) in GUI_WORKSPACES_ORDER}
            self.bar_lay = QHBoxLayout()
            self.find_input = QLineEdit(self)
            self.find_msg = QLabel(self)

            self.scroll.setWidgetResizable(True)

            #self.scroll_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

            for i in GUI_MASTERS:
                self.scroll_lay.addWidget(self.master_widget[i])
                self.master_widget[i].setLayout(self.master_lay[i])
                self.master_lay[i].setSpacing(0)
                self.master_lay[i].setContentsMargins(0, 0, 0, 0)


            for ((master, slave), widget) in self.workspaces.items():
                self.master_lay[master].addWidget(widget)

            self.find_input.setPlaceholderText("Find")
            self.find_input.textChanged.connect(self.find_changed)
            self.find_msg.setAutoFillBackground(True)

            self.scroll_widget.setLayout(self.scroll_lay)
            self.scroll.setWidget(self.scroll_widget)
            self.bar_lay.addWidget(self.find_input)
            self.bar_lay.addWidget(self.find_msg)
            self.lay.addWidget(self.scroll)
            self.lay.addItem(self.bar_lay)
            self.setLayout(self.lay)
            

            self.focused_master = None
            self.focused_slave = None
            self.focused_widget = None

            self.find_regex = None
            self.find_error = None
            self.find_matchs = []

        def focus_workspace(self, n_master, n_slave):
            def f(x):
                if self.focused_widget:
                    self.focused_widget.setColor(QColor(0,0,0))
                if n_slave <= MAX_MASTERED_SLAVE:
                    self.focused_master = n_master
                self.focused_slave = n_slave
                self.focused_widget = x
                self.scroll.ensureWidgetVisible(x)
                x.setColor(QColor(255,0,0))
                if self.find_regex:
                    self.set_find_msg()

            qt_workspace_widget_func(n_master, n_slave, f)

        def change_focused_forkspace(self, *arg, **kvarg):
            print("change_focused_forkspace", arg, kvarg, self.focused_master, self.focused_slave)
            with lock.read:
                try:
                    w = get_workspace(*arg, **kvarg, old_master=self.focused_master, old_slave=self.focused_slave, gui=True)
                except WorkspaceOutOfRange:
                    osd.notify("No more workspaces", color="magenta", to='display', min_duration=0)
                    print("change_focused_forkspace", "->", "ERR")
                    return
            print("change_focused_forkspace", "->", w)
            self.focus_workspace(*w)

        def load_i3_tree(self):
            def ppr(x, t, fl=False):
                print("  "*t, "F" if fl else "", x.type, x.name, x.layout)
                for y in x.nodes:
                    ppr(y, t+1)
                for y in x.floating_nodes:
                    ppr(y, t+1, True)
            t = i3.value.get_tree()
            # ppr(t, 0)
            def go(x):
                if x.type == "workspace":
                    qt_workspace_widget_func(*parse_workspace(x.name), lambda y: y.l_tree.set_tree(x))
                else:
                    for y in x.nodes:
                        go(y)
            go(t)

            if self.find_regex:
                for w in self.workspaces.values():
                    w.l_tree.find(self.find_regex)

        def set_screenshot_size(self, val):
            self.screenshot_size = val
            for i in self.workspaces.values():
                i.redraw_pic()
            self.focus_workspace(self.focused_master, self.focused_slave)

        def clear_find(self):
            self.find_regex = None
            self.find_error = None
            for w in self.workspaces.values():
                w.l_tree.clear_find()

        def find(self, s):
            self.clear_find()
            print("FIND", s)
            try:
                self.find_regex = regex.compile(s, regex.IGNORECASE)
            except regex.error as e:
                self.find_error = e
                self.set_find_msg()
                return
            find_error = None
            for w in self.workspaces.values():
                w.l_tree.find(self.find_regex)
            for i in GUI_WORKSPACES_ORDER:
                w = self.workspaces[i]
                if len(w.l_tree.find_matchs) > 0:
                    self.change_focused_forkspace(w.master, w.slave)
                    break
            self.set_find_msg()

        def set_find_msg(self):
            p = QPalette()
            if self.find_error:
                self.find_msg.setText(str(self.find_error))
                p.setColor(self.find_msg.backgroundRole(), QColor(255,100,0))
            elif self.find_regex:
                tot_ws = 0
                tot_win = 0
                act_ws = None
                act_win = None
                act_win_to = None
                for i in GUI_WORKSPACES_ORDER:
                    w = self.workspaces[i]
                    l = len(w.l_tree.find_matchs)
                    if l:
                        tot_ws += 1
                    if i == (self.focused_widget.master, self.focused_widget.slave):
                        act_ws = tot_ws
                        act_win = tot_win + 1
                        act_win_to = tot_win + l
                    tot_win += l
                if tot_ws:
                    self.find_msg.setText(f"{act_ws}/{tot_ws} window {act_win}-{act_win_to}/{tot_win}")
                    p.setColor(self.find_msg.backgroundRole(), QColor(0,255,0))
                else:
                    self.find_msg.setText("Not found")
                    p.setColor(self.find_msg.backgroundRole(), QColor(255,0,0))
            else:
                self.find_msg.setText("")
                p.setColor(self.find_msg.backgroundRole(), QColor(0,0,0,0))
            print("SET PALETTE", p)
            self.find_msg.setPalette(p)


        
        def find_next(self, direction):
            index = GUI_WORKSPACES_ORDER.index((self.focused_widget.master, self.focused_widget.slave))
            print("FN", direction)
            while True:
                index += direction
                try:
                    w = self.workspaces[GUI_WORKSPACES_ORDER[index]]
                except IndexError:
                    return
                if len(w.l_tree.find_matchs) > 0:
                    self.change_focused_forkspace(w.master, w.slave)
                    print("FN", w.master, w.slave)
                    return

        @pyqtSlot()
        def find_changed(self):
            s = self.find_input.text()
            if len(s) >= 3:
                self.find(s)
            else:
                self.clear_find()



        @qtoverride
        def closeEvent(self, event):
            event.ignore()

        @qtoverride
        def keyPressEvent(self, event):
            SHIFT = Qt.ShiftModifier
            CTRL = Qt.ControlModifier
            print(event, type(event), event.text(), event.key(), int(event.modifiers()))
            event.accept()
            mod = int(event.modifiers())
            key = int(event.key())
            if mod == 0 and key == ord('R'):
                for i in self.workspaces.values():
                    i.metadata_changed()
            if mod == 0 and key == ord('T'):
                self.load_i3_tree()
            if mod == 0 and key == ord('A'):
                try:
                    self.set_screenshot_size([x for x in SCREENSHOTS_SIZES if x > self.screenshot_size][0])
                except IndexError:
                    pass
            if mod == 0 and key == ord('S'):
                try:
                    self.set_screenshot_size([x for x in SCREENSHOTS_SIZES if x < self.screenshot_size][-1])
                except IndexError:
                    pass
            F_KEYS = {v: k+1 for k, v in enumerate([
                16777264, 16777265, 16777266, 16777267, 16777268,
                16777269, 16777270, 16777271, 16777272, 16777273,
                16777274, 16777275
            ])}
            NUM_KEYS = {ord('`'):0,
                    **{ord(str(i)): i for i in range(1, 10)},
                    ord('0'): 10, ord('-'): 11, ord('='): 12,
            }
            LEFT_KEYS = {ord('H'), Qt.Key_Left}
            UP_KEYS = {ord('J'), Qt.Key_Up}
            DOWN_KEYS = {ord('K'), Qt.Key_Down}
            RIGHT_KEYS = {ord('L'), Qt.Key_Right}
            if mod == 0 and key in ORD_TO_WORKSPACE:
                self.change_focused_forkspace(workspace_cmd=ORD_TO_WORKSPACE[key])
            if mod == 0 and key in NUM_KEYS:
                self.change_focused_forkspace(slave_cmd=NUM_KEYS[key])
            if mod == 0 and key in F_KEYS:
                self.change_focused_forkspace(master_cmd=F_KEYS[key])

            if mod == 0 and key in LEFT_KEYS:
                self.change_focused_forkspace(slave_cmd="prev-skip")
            if mod == SHIFT and key in LEFT_KEYS:
                self.change_focused_forkspace(slave_cmd="prev-limit")
            if mod == 0 and key in RIGHT_KEYS:
                self.change_focused_forkspace(slave_cmd="next-skip")
            if mod == SHIFT and key in RIGHT_KEYS:
                self.change_focused_forkspace(slave_cmd="next-limit")

            if mod == 0 and key in UP_KEYS:
                self.change_focused_forkspace(master_cmd="prev-skip")
            if mod == SHIFT and key in UP_KEYS:
                self.change_focused_forkspace(master_cmd="prev")
            if mod == 0 and key in DOWN_KEYS:
                self.change_focused_forkspace(master_cmd="next-skip")
            if mod == SHIFT and key in DOWN_KEYS:
                self.change_focused_forkspace(master_cmd="next")

            if mod == CTRL and key in LEFT_KEYS:
                self.find_next(-1)
            if mod == CTRL and key in RIGHT_KEYS:
                self.find_next(1)
            if mod == SHIFT and key == ord("N"):
                self.find_next(-1)
            if mod == 0 and key == ord("N"):
                self.find_next(1)

            if mod == 0 and key == ord('/'):
                self.find_input.setFocus()
            print(key, 6777216 == key)
            if mod == 0 and key == 16777216:  # ESCAPE
                if app.focusWidget() == self.find_input:
                    self.clear_find()
                    self.find_input.setText("")
                    self.find_error = None
                    self.set_find_msg()
                if app.focusWidget() == self.scroll:
                    with lock.read:
                        w = get_workspace()
                    i3.value.command(f'workspace {workspace(*w)}')
                else:
                    self.scroll.setFocus()
            if mod == 0 and key == 16777220:  # ENTER
                if app.focusWidget() == self.find_input:
                    self.scroll.setFocus()
                else:
                    i3.value.command(f'workspace {workspace(self.focused_master, self.focused_slave)}')

    m_win = MainWindow()
    m_win.show()

    with lock:
        load()

    app.exec_()


######################################
######################################
######################################

def x_main():
    i3.value = i3ipc.Connection()

    load()

    goto_workspace(1, 1)

    for msg in get_queue():
        print(msg)
        if len(msg) >= 1:
            try:
                with lock:
                    main_functions[msg[0]](msg)
            except WorkspaceOutOfRange:
                osd.notify("No more workspaces", color="magenta", to='display', min_duration=0)
            except Exception as e:
                traceback.print_exc()

i3_watch_thread = threading.Thread(target=i3_watch)
i3_watch_thread.daemon = True
i3_watch_thread.start()

# qt_thread = threading.Thread(target=qt_main)
# qt_thread.daemon = True
# qt_thread.start()

if USE_QT:
    x_thread = threading.Thread(target=x_main)
    x_thread.daemon = True
    x_thread.start()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    qt_main()
else:
    x_main()
