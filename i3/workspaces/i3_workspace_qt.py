#!/usr/bin/env python3
import sys
import os
import osd
import threading
from collections import defaultdict
import binascii

import Xlib
import Xlib.display
import Xlib.X

import argparse

import i3ipc
import time
import traceback
from dataclasses import dataclass

import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import re

from i3_workspace_shared import *
from i3_workspace_lib import *
import i3_workspace_help as help
from i3_workspace_constants import *

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


def qt_main():


    shared.i3.value = i3ipc.Connection()
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
        return f(m_win._workspaces[(master, slave)])

    SCREENSHOTS_SIZES = [120, 150, 200, 250, 300, 400, 500, 750, 1000]

    # An object containing methods you want to run in a thread
    class Tasker(QObject):
        do = pyqtSignal(object)
        func = {}

        def f(self, *arg):
            self.do.emit(arg)

        @pyqtSlot(object)
        def _run(self, w):
            #print(f"QT TASK SLOT {threading.current_thread()}: {w}")
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
                shared.i3.value.command(f'workspace {workspace(n_master, n_slave)}')
                if (n_master, n_slave) == GUI_WORKSPACE:
                    m_win.move_to_gui_workspace()


            @func_add
            def gui_focused():
                m_win.load_i3_tree()
                with shared.lock.read:
                    w = get_workspace()
                m_win.focus_workspace(*w)

    shared.qt_thread_tasker = Tasker()

    class I3NodeWidget(QWidget):
        def __init__(self, t, parent=None):
            super().__init__(parent)
            self.container_id = t.id

        @qtoverride
        def mousePressEvent(self, event):
            print(event, type(event), event.pos(), int(event.flags()), event.buttons())
            event.accept()
            shared.i3.value.command(f'[con_id={self.container_id}] focus')

    class I3WindowNodeWidget(I3NodeWidget):
        def __init__(self, t, parent=None):
            super().__init__(t, parent)
            self._hlay = no_space(QHBoxLayout(self))
            self._name = QLabel(self)
            self.title = t.name
            self._title = QLabel(self)
            self._title.setText(t.name)
            self.setAutoFillBackground(True)
            self.setLayout(self._hlay)
            self._hlay.addWidget(self._title)

    class I3InnerNodeWidget(I3NodeWidget):
        def __init__(self, t, parent=None):
            super().__init__(t, parent)
            self._hlay = no_space(QHBoxLayout(self))
            self._head = QLabel(self)
            self._list = no_space(QVBoxLayout())

            self.setLayout(self._hlay)
            self._hlay.addWidget(self._head)
            self._hlay.addItem(self._list)

            self._head.setText({
                "splith": "H",
                "splitv": "V",
                "tabbed": "T",
                "stacked": "S"
            }.get(t.layout, "?"))
            self._head.setFixedWidth(13)

            self.nodes = [i3_tree_widget_create(i, self) for i in t.nodes]
            for i in self.nodes:
                self._list.addWidget(i)

    def i3_tree_widget_create(t, parent):
        if t.nodes:
            return I3InnerNodeWidget(t, parent)
        else:
            return I3WindowNodeWidget(t, parent)

    class I3TreeWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._lay = no_space(QVBoxLayout(self))
            self.setLayout(self._lay)
            self.all_inner_nides = []
            self.all_window_nodes = []
            self.find_matchs = []

        def clear(self):
            while (i := self._lay.takeAt(0)):
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
            self._lay.addWidget(r)
            for i in t.floating_nodes:
                for j in i.nodes:
                    f = i3_tree_widget_create(j, self)
                    go(f)
                    self._lay.addWidget(f)

        def find(self, r):
            for win in self.all_window_nodes:
                m = r.search(win.title)
                if m:
                    span = m.span()

                    t = win.title
                    win._title.setText(t[:span[0]] + "<b>" + t[span[0]:span[1]] + "</b>" + t[span[1]:])
                    p = QPalette()
                    p.setColor(win.backgroundRole(), QColor(255,255,0))
                    win.setPalette(p)
                    self.find_matchs.append((win, m))

        def clear_find(self):
            for win,m in self.find_matchs:
                p = QPalette()
                p.setColor(win.backgroundRole(), QColor(0,0,0,0))
                win.setPalette(p)
                win._title.setText(win.title)
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
            self._lay = no_space(QVBoxLayout(self))
            self._name = QLabel(self)
            self._screenshot = QLabel(self)
            self._tree = I3TreeWidget(self)


            self._lay.addWidget(self._name)
            self._lay.addWidget(self._screenshot)
            self._lay.addWidget(self._tree)
            self._lay.addStretch()
            self.setLayout(self._lay)
            self._name.setAlignment(Qt.AlignCenter)


            self.metadata_changed()

        @qtoverride
        def mousePressEvent(self, event):
            print(event, type(event), event.pos(), int(event.flags()), event.buttons())
            event.accept()
            shared.i3.value.command(f'workspace {workspace(self.master, self.slave)}')

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
                self._screenshot.setPixmap(s)
                self._screenshot.setScaledContents(False)
            else:
                self._screenshot.clear()

        def make_screenshot(self):
            self.exist = True
            with shared.lock.read:
                try:
                    o = shared.output_of_workspace[self.master][self.slave]
                    rect = shared.outputs[o].rect
                except KeyError:
                    traceback.print_exc()
                    return
            self.screenshot = s.grabWindow(QApplication.desktop().winId(), rect.x, rect.y, rect.width, rect.height)
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
            self._tree.clear()

        def metadata_changed(self):
            self._name.setText(f"<b>{workspace(self.master, self.slave)}")
            p_name = QPalette()
            p_name.setColor(QPalette.WindowText, QColor(0,0,0))

            self._name.setAutoFillBackground(True)
            with shared.lock.read:
                try:
                    if shared.outputs[shared.output_of_workspace[self.master][self.slave]].primary:
                        p_name.setColor(QPalette.Window, QColor(255, 255, 255))
                    else:
                        p_name.setColor(QPalette.Window, QColor(180, 180, 180))
                except KeyError:
                    pass
                if (self.master, self.slave) in shared.workspace_on.values():
                        p_name.setColor(QPalette.WindowText, QColor(0,255,0))
                elif self.master is not None:
                    if shared.slave_for[self.master] == self.slave:
                        p_name.setColor(QPalette.WindowText, QColor(255,0,0))
                    else:
                        for x in shared.slave_on_for.values():
                            if x is not None and x[self.master] == self.slave:
                                p_name.setColor(QPalette.WindowText, QColor(0,0,255))
                                break

            self._name.setPalette(p_name)

        def parse_i3_tree(self, t):
            s = ""
            print(s)
            self._tree.set_tree(t)

        def setColor(self, color):
            pal = self.palette()
            pal.setColor(QPalette.WindowText, color)
            self.setPalette(pal)


    class TextShowWidget(QWidget):
        def __init__(self, text, parent=None):
            super().__init__(parent)

            self._lay = no_space(QVBoxLayout(self))
            self._text_area = QTextBrowser(self)
            self._bar_lay = QHBoxLayout()
            self._find_input = QLineEdit(self)
            self._find_msg = QLabel(self)

            self._find_input.setPlaceholderText("Find")
            self._find_msg.setAutoFillBackground(True)

            self._bar_lay.addWidget(self._find_input)
            self._bar_lay.addWidget(self._find_msg)
            self._lay.addWidget(self._text_area)
            self._lay.addItem(self._bar_lay)
            self.setLayout(self._lay)

            self._find_input.setFocus()
            self._find_input.textChanged.connect(self.find_changed)

            self._text_area.setReadOnly(True)
            self._text_area.setPlainText(text)
            self.html = self._text_area.toHtml()
            self.find_error = None
            self.find_count = None

        def find(self, s):
            def parse_html(html):
                strings = []
                tags = []
                i = 0
                while True:
                    l = html.find('<', i)
                    if l == -1:
                        strings.append(html[i:])
                        break
                    r = html.find('>', l)
                    strings.append(html[i:l])
                    tags.append(html[l:r+1])
                    i = r + 1
                return strings, tags

            self.clear_find()
            try:
                find_regex = re.compile(s, re.IGNORECASE)
            except re.error as e:
                self.find_error = e
                self.set_find_msg()
                return
            find_error = None
            self.find_count = 0
            def mark_find(s):
                m = find_regex.search(s)
                if m:
                    span = m.span()
                    self.find_count += 1
                    s = s[:span[0]] + '<span style="background-color:#FFCC00">' + s[span[0]:span[1]] + "</span>" + mark_find(s[span[1]:])
                return s
            strings, tags = parse_html(self.html)
            x = "".join([a+b for (a,b) in zip(tags + [], map(mark_find, strings))])
            self._text_area.setHtml(x)

            self.set_find_msg()

        def clear_find(self):
            self.find_count = None
            self._text_area.setHtml(self.html)

        def set_find_msg(self):
            p = QPalette()
            if self.find_error:
                self._find_msg.setText(str(self.find_error))
                p.setColor(self._find_msg.backgroundRole(), QColor(255,100,0))
            elif self.find_count is None:
                self._find_msg.setText(f"")
                p.setColor(self._find_msg.backgroundRole(), QColor(255,255,255))
            elif self.find_count > 0:
                self._find_msg.setText(f"{self.find_count}")
                p.setColor(self._find_msg.backgroundRole(), QColor(0,255,0))
            else:
                self._find_msg.setText("Not found")
                p.setColor(self._find_msg.backgroundRole(), QColor(255,0,0))
            self._find_msg.setPalette(p)

        @pyqtSlot()
        def find_changed(self):
            s = self._find_input.text()
            if len(s) >= 3:
                self.find(s)
            else:
                self.clear_find()

    class MainWindow(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.setWindowTitle("i3-workspace-daemon")

            self.screenshot_size = 300

            self._lay = no_space(QVBoxLayout(self))
            self._scroll = QNoArrowScrollArea(self)
            self._scroll_widget = QWidget(self)
            self._scroll_lay = no_space(QVBoxLayout(self._scroll_widget))
            self._master_widgets = {i: QWidget(self) for i in GUI_MASTERS}
            self._master_lays = {i: FlowLayout(self._master_widgets[i]) for i in GUI_MASTERS}
            self._workspaces = {(master,slave): WorkspaceWidget(master, slave, self) for (master, slave) in GUI_WORKSPACES_ORDER}
            self._bar_lay = QHBoxLayout()
            self._help_label = QPushButton(self)
            self._find_input = QLineEdit(self)
            self._find_msg = QLabel(self)
            self._help_label.clicked.connect(self._find_msg_clicked)

            self._scroll.setWidgetResizable(True)

            #self.scroll_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

            for i in GUI_MASTERS:
                self._scroll_lay.addWidget(self._master_widgets[i])
                self._master_widgets[i].setLayout(self._master_lays[i])
                self._master_lays[i].setSpacing(0)
                self._master_lays[i].setContentsMargins(0, 0, 0, 0)


            for ((master, slave), widget) in self._workspaces.items():
                self._master_lays[master].addWidget(widget)

            self._find_input.setPlaceholderText("Find")
            self._find_input.textChanged.connect(self.find_changed)
            self._find_msg.setAutoFillBackground(True)

            self._help_label.setText("Help (?)")
            self._help_label.setFocusPolicy(Qt.NoFocus)

            self._scroll_widget.setLayout(self._scroll_lay)
            self._scroll.setWidget(self._scroll_widget)
            self._bar_lay.addWidget(self._help_label)
            self._bar_lay.addWidget(self._find_input)
            self._bar_lay.addWidget(self._find_msg)
            self._lay.addWidget(self._scroll)
            self._lay.addItem(self._bar_lay)
            self.setLayout(self._lay)

            self.focused_master = None
            self.focused_slave = None
            self.focused_widget = None

            self.find_regex = None
            self.find_error = None
            self.find_matchs = []

            self._help_window = TextShowWidget(help.qt)

        @pyqtSlot(bool)
        def _find_msg_clicked(self, x):
            self.show_help()

        def focus_workspace(self, n_master, n_slave):
            def f(x):
                if self.focused_widget:
                    self.focused_widget.setColor(QColor(0,0,0))
                if n_slave <= MAX_MASTERED_SLAVE:
                    self.focused_master = n_master
                self.focused_slave = n_slave
                self.focused_widget = x
                self._scroll.ensureWidgetVisible(x)
                x.setColor(QColor(255,0,0))
                if self.find_regex:
                    self.set_find_msg()

            qt_workspace_widget_func(n_master, n_slave, f)

        def change_focused_forkspace(self, *arg, **kvarg):
            print("change_focused_forkspace", arg, kvarg, self.focused_master, self.focused_slave)
            with shared.lock.read:
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
            t = shared.i3.value.get_tree()
            # ppr(t, 0)
            def go(x):
                if x.type == "workspace":
                    qt_workspace_widget_func(*parse_workspace(x.name), lambda y: y._tree.set_tree(x))
                else:
                    for y in x.nodes:
                        go(y)
            go(t)

            if self.find_regex:
                for w in self._workspaces.values():
                    w._tree.find(self.find_regex)

        def set_screenshot_size(self, val):
            self.screenshot_size = val
            for i in self._workspaces.values():
                i.redraw_pic()
            self.focus_workspace(self.focused_master, self.focused_slave)

        def clear_find(self):
            self.find_regex = None
            self.find_error = None
            for w in self._workspaces.values():
                w._tree.clear_find()

        def find(self, s):
            self.clear_find()
            print("FIND", s)
            try:
                self.find_regex = re.compile(s, re.IGNORECASE)
            except re.error as e:
                self.find_error = e
                self.set_find_msg()
                return
            find_error = None
            for w in self._workspaces.values():
                w._tree.find(self.find_regex)
            for i in GUI_WORKSPACES_ORDER:
                w = self._workspaces[i]
                if len(w._tree.find_matchs) > 0:
                    self.change_focused_forkspace(w.master, w.slave)
                    break
            self.set_find_msg()

        def set_find_msg(self):
            p = QPalette()
            if self.find_error:
                self._find_msg.setText(str(self.find_error))
                p.setColor(self._find_msg.backgroundRole(), QColor(255,100,0))
            elif self.find_regex:
                tot_ws = 0
                tot_win = 0
                act_ws = None
                act_win = None
                act_win_to = None
                for i in GUI_WORKSPACES_ORDER:
                    w = self._workspaces[i]
                    l = len(w._tree.find_matchs)
                    if l:
                        tot_ws += 1
                    if i == (self.focused_widget.master, self.focused_widget.slave):
                        act_ws = tot_ws
                        act_win = tot_win + 1
                        act_win_to = tot_win + l
                    tot_win += l
                if tot_ws:
                    self._find_msg.setText(f"{act_ws}/{tot_ws} window {act_win}-{act_win_to}/{tot_win}")
                    p.setColor(self._find_msg.backgroundRole(), QColor(0,255,0))
                else:
                    self._find_msg.setText("Not found")
                    p.setColor(self._find_msg.backgroundRole(), QColor(255,0,0))
            else:
                self._find_msg.setText("")
                p.setColor(self._find_msg.backgroundRole(), QColor(0,0,0,0))
            print("SET PALETTE", p)
            self._find_msg.setPalette(p)


        def find_next(self, direction):
            index = GUI_WORKSPACES_ORDER.index((self.focused_widget.master, self.focused_widget.slave))
            print("FN", direction)
            while True:
                index += direction
                try:
                    w = self._workspaces[GUI_WORKSPACES_ORDER[index]]
                except IndexError:
                    return
                if len(w._tree.find_matchs) > 0:
                    self.change_focused_forkspace(w.master, w.slave)
                    print("FN", w.master, w.slave)
                    return

        @pyqtSlot()
        def find_changed(self):
            s = self._find_input.text()
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
            print(event, type(event), event.text(), event.key(), int(event.modifiers()))
            mod = int(event.modifiers())
            key = int(event.key())

            event.accept()
            def keyPressEvent_main(key, mod):
                if key == ord('?') and mod == SHIFT:
                    self.show_help()
                elif mod == 0 and key == ord('R'): # Undocumented
                    for i in self._workspaces.values():
                        i.metadata_changed()
                elif mod == 0 and key == ord('T'):
                    self.load_i3_tree()
                elif mod == 0 and key == ord('W'):
                    try:
                        self.set_screenshot_size([x for x in SCREENSHOTS_SIZES if x > self.screenshot_size][0])
                    except IndexError:
                        pass
                elif mod == 0 and key == ord('E'):
                    try:
                        self.set_screenshot_size([x for x in SCREENSHOTS_SIZES if x < self.screenshot_size][-1])
                    except IndexError:
                        pass
                elif mod == 0 and key in ORD_TO_WORKSPACE:
                    self.change_focused_forkspace(workspace_cmd=ORD_TO_WORKSPACE[key])
                elif mod == 0 and key in NUM_KEYS:
                    self.change_focused_forkspace(slave_cmd=NUM_KEYS[key])
                elif mod == 0 and key in F_KEYS:
                    self.change_focused_forkspace(master_cmd=F_KEYS[key])

                elif mod == 0 and key in LEFT_KEYS:
                    self.change_focused_forkspace(slave_cmd="prev-skip")
                elif mod == SHIFT and key in LEFT_KEYS:
                    self.change_focused_forkspace(slave_cmd="prev-limit")
                elif mod == 0 and key in RIGHT_KEYS:
                    self.change_focused_forkspace(slave_cmd="next-skip")
                elif mod == SHIFT and key in RIGHT_KEYS:
                    self.change_focused_forkspace(slave_cmd="next-limit")

                elif mod == 0 and key in UP_KEYS:
                    self.change_focused_forkspace(master_cmd="prev-skip")
                elif mod == SHIFT and key in UP_KEYS:
                    self.change_focused_forkspace(master_cmd="prev")
                elif mod == 0 and key in DOWN_KEYS:
                    self.change_focused_forkspace(master_cmd="next-skip")
                elif mod == SHIFT and key in DOWN_KEYS:
                    self.change_focused_forkspace(master_cmd="next")

                elif mod == CTRL and key in LEFT_KEYS:
                    self.find_next(-1)
                elif mod == CTRL and key in RIGHT_KEYS:
                    self.find_next(1)
                elif mod == SHIFT and key == ord("N"):
                    self.find_next(-1)
                elif mod == 0 and key == ord("N"):
                    self.find_next(1)

                elif mod == 0 and key == ord('/'):
                    self._find_input.setFocus()
                elif mod == 0 and key == 16777216:  # ESCAPE
                    with shared.lock.read:
                        w = get_workspace()
                    shared.i3.value.command(f'workspace {workspace(*w)}')
                elif mod == 0 and key == 16777220:  # ENTER
                    shared.i3.value.command(f'workspace {workspace(self.focused_master, self.focused_slave)}')

            def keyPressEvent_find(key, mod):
                if mod == 0 and key == 16777216:  # ESCAPE
                    self.clear_find()
                    self._find_input.setText("")
                    self.find_error = None
                    self.set_find_msg()
                    self._scroll.setFocus()
                elif mod == 0 and key == 16777220:  # ENTER
                    self._scroll.setFocus()
                elif mod == 0 and key == Qt.Key_Up:
                    self.find_next(-1)
                elif mod == 0 and key == Qt.Key_Down:
                    self.find_next(1)
                else:
                    print("CMCT", mod, mod & ~CTRL)
                    keyPressEvent_main(key, mod & ~CTRL)
            if app.focusWidget() == self._find_input:
                keyPressEvent_find(key, mod)
            else:
                keyPressEvent_main(key, mod)

        def show_help(self):
            self._help_window.show()

        def move_to_gui_workspace(self):
            print(shared.i3.value.command(f'[id={int(self.winId())}] move container to workspace 0'))

    m_win = MainWindow()
    m_win.show()
    m_win.move_to_gui_workspace()

    with shared.lock:
        load_workspaces()

    app.exec_()
