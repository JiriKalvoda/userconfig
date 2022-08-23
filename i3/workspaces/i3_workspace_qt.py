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
import random
import string

from i3_workspace_shared import *
from i3_workspace_lib import *
import i3_workspace_help as help
from i3_workspace_constants import *

def p(x):
    # print i3msg reply
    for i in x:
        print(i.__dict__)

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

class DragFeature(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.press_event_pos = None
        self.press_event_buttons = None


    @qtoverride
    def mousePressEvent(self, event):
        event.accept()
        self.press_event_pos = event.pos()
        self.press_event_buttons = event.buttons()

    @qtoverride
    def mouseReleaseEvent(self, event):
        if self.press_event_pos is not None:
            if (event.pos() - self.press_event_pos).manhattanLength() < QApplication.startDragDistance():
                self.clicked(self.press_event_pos, self.press_event_buttons)
            self.press_event_pos = None

    @qtoverride
    def mouseMoveEvent(self, event):
        if self.press_event_pos is not None:
            if (event.pos() - self.press_event_pos).manhattanLength() >= QApplication.startDragDistance():
                self.drag(self.press_event_pos, self.press_event_buttons)
                self.press_event_pos = None
        event.accept()

    def clicked(self, pos, buttons):
        pass

    def drag(self, pos, buttons):
        d = QDrag(self)
        mimeData = QMimeData()
        d.setMimeData(mimeData)

        dropAction = d.exec()

def get_shortcuts(counts_by_priority):
    max_depths = []
    depth = 0
    empty = 1
    keys = "fjdkslaqpwoeirughtyvncmbxz"
    ab_len = len(keys)
    for i in counts_by_priority:
        while 2 * i > empty: # use at most 1/2 of empty keys
            depth += 1
            empty *= ab_len
        empty -= i
        max_depths.append(depth)
    to_use = [""]
    to_use_index = 0
    for count, max_depth in zip(counts_by_priority, max_depths):
        for i in range(count):
            d = max_depth
            upgrade_eat_empty = (ab_len - 1) * ab_len**(depth - d)
            if empty >= upgrade_eat_empty:
                d -= 1
                empty -= upgrade_eat_empty
            while len(to_use[to_use_index]) < d:
                to_use += [to_use[to_use_index] + x for x in keys]
                to_use_index += 1
            yield to_use[to_use_index]
            to_use_index += 1
            

    reaming_options = len(keys)**max_depth
    reaming_shortcuts = sum(counts_by_priority)



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
                shared.i3_cmd(f'workspace {workspace(n_master, n_slave)}')
                if (n_master, n_slave) == GUI_WORKSPACE:
                    m_win.move_to_gui_workspace()

            @func_add
            def screenshot(master, slave):
                qt_workspace_widget_func(master, slave, lambda x: x.make_screenshot())

            @func_add
            def gui_focused():
                m_win.load_i3_tree()
                with shared.lock.read:
                    w = get_workspace()
                m_win.focus_workspace(*w)

    shared.qt_thread_tasker = Tasker()

    class TmpWin(QWidget):
        def __init__(self):
            self.title = "i3-workspace-daemon-tmp-window-" + ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(15))
            super().__init__()
            self.setWindowTitle(self.title)
            self.show()
            self.id = int(self.winId())
            shared.i3_cmd(f'[id={self.id}] move container to workspace tmp')


    class I3NodeWidget(QFrame, DragFeature):
        def __init__(self, t, workspace_widget, parent=None):
            super().__init__(parent)
            self.workspace_widget = workspace_widget
            self.container_id = t.id
            self.shortcut = None

            self.setObjectName(f"{id(self)}");

            self.setAcceptDrops(True)

            self.dropPlace = None  # 0: top 1: mid 2: bottom
            self.ignore_drop = False
            self.marked = None

        def focus(self):
            shared.i3_cmd(f'[con_id={self.container_id}] focus')

        def move_to_workspace(self, master, slave):
            self.workspace_widget.screenshot_changed()
            m_win._workspaces[(master, slave)].screenshot_changed()
            shared.i3_cmd(f'[con_id={self.container_id}] move container to workspace {workspace(master, slave)}')

        def expand_to_workspace(self, master, slave):
            self.workspace_widget.screenshot_changed()
            m_win._workspaces[(master, slave)].screenshot_changed()
            if type(self) != I3InnerNodeWidget:
                self.move_to_workspace(master, slave)
            else:
                marks = []
                for (i, it) in enumerate(self.nodes):
                    shared.i3_cmd(f'[con_id={it.container_id}] mark tmp_from_{i}')
                    marks.append(f"tmp_from_{i}")
                shared.i3_cmd(f'[con_mark="{"|".join(marks)}"] move container to to workspace {workspace(master, slave)}')

        def move_to(self, target):
            self.workspace_widget.screenshot_changed()
            target.workspace_widget.screenshot_changed()
            shared.i3_cmd(f'[con_id={target.container_id}] mark tmp')
            shared.i3_cmd(f'[con_id={self.container_id}] move container to mark tmp')

        def move_after(self, target):
            self.workspace_widget.screenshot_changed()
            target.workspace_widget.screenshot_changed()
            if type(target) == I3WindowNodeWidget:
                self.move_to(target)
            else:
                tmp_win = TmpWin()
                shared.i3_cmd(f'[con_id={target.container_id}] swap container with id {tmp_win.id}')
                shared.i3_cmd(f'[id={tmp_win.id}] mark tmp')
                shared.i3_cmd(f'[con_id={self.container_id}] move container to mark tmp')
                try:
                    shared.i3_cmd(f'[con_id={target.container_id}] swap container with id {tmp_win.id}')
                except I3CmdException:
                    pass  # Could fail whem moving the only window from container to upper container

        def move_before(self, target):
            self.move_after(target)
            target.move_after(self)
            # target.move_to(self)
            # if type(self) == I3InnerNodeWidget:
                # p = target.parentWidget()
                # print("A")
                # if isinstance(p, I3InnerNodeWidget):
                    # print("B")
                    # target.move_to(p)


        def expand_after(self, target):
            self.workspace_widget.screenshot_changed()
            target.workspace_widget.screenshot_changed()
            if type(self) != I3InnerNodeWidget:
                self.move_after(target)
            else:
                marks = []
                for (i, it) in enumerate(self.nodes):
                    shared.i3_cmd(f'[con_id={it.container_id}] mark tmp_from_{i}')
                    marks.append(f"tmp_from_{i}")
                if type(target) == I3WindowNodeWidget:
                    tmp_win = TmpWin()
                    shared.i3_cmd(f'[con_id={target.container_id}] swap container with id {tmp_win.id}')
                    shared.i3_cmd(f'[id={tmp_win.id}] mark tmp')
                else:
                    shared.i3_cmd(f'[con_id={target.container_id}] mark tmp')
                shared.i3_cmd(f'[con_mark="{"|".join(marks)}"] move container to mark tmp')
                if type(target) == I3WindowNodeWidget:
                    shared.i3_cmd(f'[con_id={target.container_id}] swap container with id {tmp_win.id}')

        def expand_before(self, target):
            if type(self) != I3InnerNodeWidget:
                self.move_before(target)
            else:
                self.expand_after(target)
                target.move_before(self.nodes[0])

        def move_to_new_container_with(self, target, orientation=None, before=False, expand=False):
            target.put_in_new_container(orientation)
            getattr(self, f'{"expand" if expand else "move"}_{"before" if before else "after"}')(target)
            #if before:
            #    self.move_to(target)
            #    t_new = shared.i3.value.get_tree()
            #    container_id = t_new.find_by_id(target.container_id).parent.id
            #    shared.i3_cmd(f'[con_id={container_id}] mark tmp')
            #    if type(target) == I3InnerNodeWidget:
            #        shared.i3_cmd(f'[con_id={self.container_id}] move container to mark tmp')
            #        print("ZDE")
            #    target.move_to(self)
            #    if type(self) == I3InnerNodeWidget:
            #        print("ZDE4")
            #        shared.i3_cmd(f'[con_id={target.container_id}] move container to mark tmp')
            #else:
            #    if type(target) == I3WindowNodeWidget:
            #        self.move_after(target)
            #    else:
            #        self.move_to(target)
            #        t_new = shared.i3.value.get_tree()
            #        container_id = t_new.find_by_id(target.container_id).parent.id
            #        shared.i3_cmd(f'[con_id={container_id}] mark tmp')
            #        shared.i3_cmd(f'[con_id={self.container_id}] move container to mark tmp')

        def do_float(self, state=None):
            self.workspace_widget.screenshot_changed()
            shared.i3_cmd(f'[con_id={self.container_id}] floating { {None:"toggle", True:"enable", False:"disable"}[state] }')

        def put_in_new_container(self, orientation=None):
            if orientation is None:
                shared.i3_cmd(f'[con_id={self.container_id}] split toggle')
            elif orientation == "splith":
                shared.i3_cmd(f'[con_id={self.container_id}] split horizontal')
            elif orientation == "splitv":
                shared.i3_cmd(f'[con_id={self.container_id}] split vertical')
            else:
                shared.i3_cmd(f'[con_id={self.container_id}] split vertical')
                shared.i3_cmd(f'[con_id={self.container_id}] layout {orientation}')

        def clicked(self, pos, buttons):
            try:
                if buttons == Qt.LeftButton:
                    self.focus()
                if buttons == Qt.MiddleButton:
                    self.do_float()
                    m_win.load_i3_tree()
            except I3CmdException as e:
                m_win.cmd_msg(e.error, QColor(255, 100, 100))
                traceback.print_exc()
                m_win.load_i3_tree()

        def drag(self, pos, buttons):
            d = QDrag(self)
            mimeData = QMimeData()
            d.setMimeData(mimeData)
            self.marked = QColor(255,0,0)
            self.redraw()

            dropAction = d.exec()

            self.marked = None
            self.redraw()


        @qtoverride
        def dragEnterEvent(self, event):
            s = event.source()
            if s is not None and isinstance(s, WorkspaceWidget) or isinstance(s, I3NodeWidget):
                self.ignore_drop = False
                x = self
                while x is not None:
                    if x == s:
                        self.ignore_drop = True
                    x = x.parentWidget()
                event.acceptProposedAction()


        @qtoverride
        def dropEvent(self, event):
            if self.ignore_drop:
                return
            s = event.source()
            if isinstance(s, WorkspaceWidget) or isinstance(s, I3NodeWidget):
                m_win.cmd_msg_clean()
                button = s.press_event_buttons
                try:
                    if isinstance(s, WorkspaceWidget):
                        for f in s._tree.floating_nodes:
                            f.move_to_workspace(self.workspace_widget.master, self.workspace_widget.slave)
                        s = s._tree.root_node
                        if s is None: return
                    if s.press_event_buttons == Qt.RightButton:
                        [s.expand_before, lambda self: s.move_to_new_container_with(self, expand=True), s.expand_after][self.drop_place](self)
                    else:
                        [s.move_before, s.move_to_new_container_with, s.move_after][self.drop_place](self)
                    m_win.load_i3_tree()
                    self.setStyleSheet(f"")
                    self.redraw()
                except I3CmdException as e:
                    m_win.cmd_msg(e.error, QColor(255, 100, 100))
                    traceback.print_exc()
                    m_win.load_i3_tree()

        @qtoverride
        def dragLeaveEvent(self, event):
            self.setStyleSheet(f"")
            self.redraw()


        @qtoverride
        def dragMoveEvent(self, event):
            event.acceptProposedAction()
            if self.ignore_drop:
                return
            y = event.answerRect().center().y()
            h = self.height()
            if y < h//4:
                self.drop_place = 0
            elif y >= h - h//4:
                self.drop_place = 2
            else:
                self.drop_place = 1
            s = event.source()
            if s is not None and isinstance(s, WorkspaceWidget) or isinstance(s, I3NodeWidget):
                style = ["border-top: 3px solid green;", "background-color: green;", "border:no; border-bottom: 3px solid green;"][self.drop_place]
                self.setStyleSheet(f"#{id(self)} {{ {style} }}");

    class I3WindowNodeWidget(I3NodeWidget):
        def __init__(self, t, workspace_widget, parent=None):
            super().__init__(t, workspace_widget, parent)
            self._hlay = no_space(QHBoxLayout(self))
            self._name = QLabel(self)
            self.title = t.name
            self.urgent = t.urgent
            self.title_with_find = None
            self._title = QLabel(self)
            self.setAutoFillBackground(True)
            self.setLayout(self._hlay)
            self._hlay.addWidget(self._title)
            self.redraw()

        def redraw(self):
            p = QPalette()
            if self.title_with_find is not None:
                t = self.title_with_find
                p.setColor(self.backgroundRole(), QColor(255, 255, 0))
            else:
                t = self.title
            if self.urgent:
                p.setColor(self.foregroundRole(), QColor(255, 0, 0))
            else:
                p.setColor(self.foregroundRole(), QColor(0, 0, 0))
            if self.marked is not None:
                p.setColor(self.backgroundRole(), self.marked)
            if self.shortcut is not None:
                self._title.setText(f"[{self.shortcut}] {t}")
            else:
                self._title.setText(self.title)
            self.setPalette(p)

            


    class I3InnerNodeWidget(I3NodeWidget):
        def __init__(self, t, workspace_widget, parent=None):
            super().__init__(t, workspace_widget, parent)
            self._hlay = no_space(QHBoxLayout(self))
            self._head = QLabel(self)
            self._list = no_space(QVBoxLayout())

            self.setAutoFillBackground(True)

            self.setLayout(self._hlay)
            self._hlay.addWidget(self._head)
            self._hlay.addItem(self._list)

            self._head.setFixedWidth(13)
            self.layout = t.layout

            self.nodes = [i3_tree_widget_create(i, workspace_widget, self) for i in t.nodes]
            for i in self.nodes:
                self._list.addWidget(i)
            self.redraw()

        def redraw(self):
            p = QPalette()
            p.setColor(self._head.foregroundRole(), QColor(0, 0, 0))
            if self.marked is not None:
                p.setColor(self.backgroundRole(), self.marked)
            if self.shortcut is not None:
                self._head.setText(f"{self.shortcut}")
            else:
                self._head.setText({
                    "splith": "H",
                    "splitv": "V",
                    "tabbed": "T",
                    "stacked": "S"
                }.get(self.layout, "?"))
            self.setPalette(p)

        def change_layout(self, new_layout=None):
            if new_layout is None:
                new_layout = {
                        "splith": "splitv",
                        "splitv": "tabbed",
                        "tabbed": "stacked",
                        "stacked": "splith",
                        }.get(self.layout, "splith")
            shared.i3_cmd(f'[con_id={self.nodes[0].container_id}] layout {new_layout}')
            self.layout = new_layout
            self.redraw()

        def clicked(self, pos, buttons):
            if buttons == Qt.RightButton:
                self.change_layout()
            else:
                super().clicked(pos, buttons)

    def i3_tree_widget_create(t, workspace_widget, parent):
        if t.nodes:
            return I3InnerNodeWidget(t, workspace_widget, parent)
        else:
            return I3WindowNodeWidget(t, workspace_widget, parent)

    class I3TreeWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.workspace_widget = parent
            self._lay = no_space(QVBoxLayout(self))
            self.setLayout(self._lay)
            self.root_node = None
            self.floating_nodes = []
            self.all_inner_nides = []
            self.all_window_nodes = []
            self.find_matchs = []
            self.container_id = None

        def clear(self):
            while (i := self._lay.takeAt(0)):
                i.widget().hide()
            self.all_inner_nides = []
            self.all_window_nodes = []
            self.find_matchs = []
            self.container_id = None
            self.all_inner_nides = []
            self.root_node = None
            self.floating_nodes = []

        def set_tree(self, t):
            self.clear()
            self.container_id = t.id
            def go(x):
                if isinstance(x, I3WindowNodeWidget):
                    self.all_window_nodes.append(x)
                if isinstance(x, I3InnerNodeWidget):
                    self.all_inner_nides.append(x)
                    for i in x.nodes:
                        go(i)
            r = i3_tree_widget_create(t, self.workspace_widget, self)
            self.root_node = r
            go(r)
            self._lay.addWidget(r)
            for i in t.floating_nodes:
                for j in i.nodes:
                    f = i3_tree_widget_create(j, self.workspace_widget, self)
                    go(f)
                    self._lay.addWidget(f)
                    self.floating_nodes.append(f)

        def find(self, r):
            for win in self.all_window_nodes:
                t = win.title
                m = r.search(t)
                if m:
                    span = m.span()
                    win.title_with_find = t[:span[0]] + "<b>" + t[span[0]:span[1]] + "</b>" + t[span[1]:]
                    win.redraw()
                    self.find_matchs.append((win, m))

        def clear_find(self):
            for win,m in self.find_matchs:
                win.title_with_find = None
                win.redraw()
            self.find_matchs = []



    class WorkspaceWidget(QFrame, DragFeature):
        screenshot = None
        screenshot_is_old = False
        exist = False

        def __init__(self, master, slave, parent):
            super().__init__(parent)
            self.setFrameShape(QFrame.Box)
            self.master = master
            self.slave = slave
            self._lay = no_space(QVBoxLayout(self))
            self._name = QLabel(self)
            self._screenshot = QLabel(self)
            self._tree = I3TreeWidget(self)

            self.setAutoFillBackground(True)
            self._name.setAutoFillBackground(True)

            self._lay.addWidget(self._name)
            self._lay.addWidget(self._screenshot)
            self._lay.addWidget(self._tree)
            self._lay.addStretch()
            self.setLayout(self._lay)
            self._name.setAlignment(Qt.AlignCenter)

            self.focused = False
            self.on_primary_output = False
            self.name_color = QColor(255, 255, 255)

            self.metadata_changed()

            self.setAcceptDrops(True)


        def redraw_pic(self):
            w = m_win.screenshot_size
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

        def redraw(self):
            p = QPalette()
            p_name = QPalette()
            p_name.setColor(self._name.foregroundRole(), self.name_color)
            if self.focused:
                p.setColor(QPalette.WindowText, QColor(255, 0, 0))
                p.setColor(self.backgroundRole(), QColor(255, 200, 200))
            else:
                if self.on_primary_output is not None:
                    if self.on_primary_output:
                        p_name.setColor(self._name.backgroundRole(), QColor(255, 255, 255))
                    else:
                        p_name.setColor(self._name.backgroundRole(), QColor(180, 180, 180))
            self.setPalette(p)
            self._name.setPalette(p_name)

        def metadata_changed(self):
            self._name.setText(f"<b>{workspace(self.master, self.slave)}")
            self.name_color = QColor(0, 0, 0)

            with shared.lock.read:
                try:
                    self.on_primary_output = shared.outputs[shared.output_of_workspace[self.master][self.slave]].primary
                except KeyError:
                    self.on_primary_output = None
                if (self.master, self.slave) in shared.workspace_on.values():
                     self.name_color = QColor(0,255,0)
                elif self.master is not None:
                    if shared.slave_for[self.master] == self.slave:
                        self.name_color =  QColor(255,0,0)
                    else:
                        for x in shared.slave_on_for.values():
                            if x is not None and x[self.master] == self.slave:
                                self.name_color = QColor(0,0,255)
            self.redraw()


        def parse_i3_tree(self, t):
            self._tree.set_tree(t)

        def clicked(self, pos, buttons):
            shared.i3_cmd(f'workspace {workspace(self.master, self.slave)}')

        @qtoverride
        def dragEnterEvent(self, event):
            s = event.source()
            if s is not None and isinstance(s, WorkspaceWidget) or isinstance(s, I3NodeWidget):
                event.acceptProposedAction()

        @qtoverride
        def dropEvent(self, event):
            s = event.source()
            if isinstance(s, WorkspaceWidget) or isinstance(s, I3NodeWidget):
                m_win.cmd_msg_clean()
                button = s.press_event_buttons
                try:
                    if isinstance(s, WorkspaceWidget):
                        for f in s._tree.floating_nodes:
                            f.move_to_workspace(self.master, self.slave)
                        s = s._tree.root_node
                        if s is None: return
                        if button == Qt.RightButton:
                            s.expand_to_workspace(self.master, self.slave)
                        else:
                            if len(s.nodes) == 1:
                                s.nodes[0].move_to_workspace(self.master, self.slave)
                            else:
                                s.move_to_workspace(self.master, self.slave)
                    else:
                        if button == Qt.RightButton:
                            s.expand_to_workspace(self.master, self.slave)
                        else:
                            s.move_to_workspace(self.master, self.slave)
                    m_win.load_i3_tree()
                except I3CmdException as e:
                    m_win.cmd_msg(e.error, QColor(255, 100, 100))
                    traceback.print_exc()
                    m_win.load_i3_tree()

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
            self._cmd_msg = QLabel(self)

            self._cmd_msg.setFixedWidth(200)
            self._cmd_msg.setAutoFillBackground(True)
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
            self._bar_lay.addWidget(self._cmd_msg)
            self._lay.addWidget(self._scroll)
            self._lay.addItem(self._bar_lay)
            self.setLayout(self._lay)

            self.focused_master = None
            self.focused_slave = None
            self.focused_widget = None

            self.find_regex = None
            self.find_error = None
            self.find_matchs = []

            self.get_continuing_key = None
            self.get_continuing_key_readed_keys = None
            self.cmd_msg_show_get_continuing_key = False

            self._help_window = TextShowWidget(help.qt)

        @pyqtSlot(bool)
        def _find_msg_clicked(self, x):
            self.show_help()

        def focus_workspace(self, n_master, n_slave):
            def f(x):
                if self.focused_widget:
                    self.focused_widget.focused = False
                    self.focused_widget.redraw()
                if n_slave <= MAX_MASTERED_SLAVE:
                    self.focused_master = n_master
                self.focused_slave = n_slave
                self.focused_widget = x
                self._scroll.ensureWidgetVisible(x)
                x.focused = True
                x.redraw()
                if self.find_regex:
                    self.set_find_msg()

            qt_workspace_widget_func(n_master, n_slave, f)

        def change_focused_forkspace(self, *arg, **kvarg):
            with shared.lock.read:
                try:
                    w = get_workspace(*arg, **kvarg, old_master=self.focused_master, old_slave=self.focused_slave, gui=True)
                except WorkspaceOutOfRange:
                    osd.notify("No more workspaces", color="magenta", to='display', min_duration=0)
                    return
            self.focus_workspace(*w)

        def load_i3_tree(self):
            self.end_get_continuing_key()
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

        def shortcuts_begin(self, cmd, fail=lambda: None, filter=lambda x: True, pre_filter=lambda x: True):
            by_priority = [[] for i in range(2*2*3)]
            shortcuts = {}
            def priority(m, s):
                if m == self.focused_master:
                    if s == self.focused_slave:
                        return 0
                    return 1
                return 2
            for (m, s), w in self._workspaces.items():
                for nd in w._tree.all_window_nodes:
                    if pre_filter(nd):
                        by_priority[(0 if nd.title_with_find else 6) + 2*priority(m, s)].append(nd)
                for nd in w._tree.all_inner_nides:
                    if pre_filter(nd):
                        by_priority[6 + 2*priority(m, s)+1].append(nd)
            gen = get_shortcuts([len(x) for x in by_priority])
            for x in by_priority:
                for nd in x:
                    shortcut = next(gen)
                    if filter(nd):
                        nd.shortcut = shortcut
                        shortcuts_node = shortcuts
                        for c in nd.shortcut[:-1]:
                            shortcuts_node.setdefault(c, {})
                            shortcuts_node = shortcuts_node[c]
                        shortcuts_node[nd.shortcut[-1]] = nd
                        nd.redraw()

            def shortcuts_go(key, mod):
                nonlocal shortcuts
                if key is None:
                    shortcuts_end()
                elif mod != 0 or not (ord('A') <= key and key <= ord('Z')):
                    shortcuts_end()
                else:
                    c = chr(key).lower()
                    if c not in shortcuts:
                        shortcuts_end()
                    else:
                        for (i, nd) in shortcuts.items():
                            if i == c:
                                def go(x):
                                    if type(x) == dict:
                                        for i in x.values(): go(i)
                                    else:
                                        x.shortcut = x.shortcut[1:]
                                        x.redraw()
                                go(nd)
                            else:
                                def go(x):
                                    if type(x) == dict:
                                        for i in x.values(): go(i)
                                    else:
                                        x.shortcut = None
                                        x.redraw()
                                go(nd)
                        shortcuts = shortcuts[c]
                        if type(shortcuts) != dict:
                            shortcuts_end(True)
                            return cmd(shortcuts)
                        return shortcuts_go

            def shortcuts_end(success=False):
                if not success:
                    fail()
                if shortcuts is not None:
                    def go(x):
                        if type(x) == dict:
                            for i in x.values():
                                go(i)
                        else:
                            x.shortcut = None
                            x.redraw()
                    go(shortcuts)
            return shortcuts_go

        def cmd_msg(self, msg, bg_color=None, is_get_continuing_key=False):
            self.cmd_msg_show_get_continuing_key = is_get_continuing_key
            self._cmd_msg.setText(msg)
            p = QPalette()
            if bg_color is not None:
                p.setColor(self._cmd_msg.backgroundRole(), bg_color)
            self._cmd_msg.setPalette(p)

        def cmd_msg_clean(self):
            if not self.cmd_msg_show_get_continuing_key:
                self.cmd_msg("")

        def begin_get_continuing_key(self, l, key, mod):
            self.get_continuing_key = l
            self.get_continuing_key_readed_keys = ""
            self.append_key_to_cmd_msg(key, mod)

        def end_get_continuing_key(self):
            if self.get_continuing_key is not None:
                self.get_continuing_key_readed_keys = None
                if self.cmd_msg_show_get_continuing_key:
                    self.cmd_msg("")
                get_continuing_key = self.get_continuing_key  # Prevent cyclic recursion
                self.get_continuing_key = None
                get_continuing_key(None, None)

        def append_key_to_cmd_msg(self, key, mod):
            if mod != 0 or not (ord('A') <= key and key <= ord('Z')):
                c = "?"
            else:
                c = chr(key).lower()
                if mod & Qt.ShiftModifier != 0:
                    c.upper()
            self.get_continuing_key_readed_keys += c
            self.cmd_msg(self.get_continuing_key_readed_keys + "...", QColor(200,200,255), is_get_continuing_key=True)


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
            MOD_KEYS = (16781694, 16777248, 16777249, 16777299, 16777251, 16777400)
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
            ESCAPE = 16777216;
            print(event, type(event), event.text(), event.key(), int(event.modifiers()))
            mod = int(event.modifiers())
            key = int(event.key())

            event.accept()

            if key not in MOD_KEYS:
                self.cmd_msg_clean()

            def keyPressEvent_main(key, mod):
                if mod == 0 and self.get_continuing_key is not None and key == ESCAPE:
                    self.end_get_continuing_key()
                elif self.get_continuing_key is not None:
                    if key not in MOD_KEYS:
                        self.append_key_to_cmd_msg(key, mod)
                        self.get_continuing_key = self.get_continuing_key(key, mod)
                        if self.get_continuing_key is None:
                            if self.cmd_msg_show_get_continuing_key:
                                self.cmd_msg("")
                elif key == ord('?') and mod == SHIFT:
                    self.show_help()
                elif mod == 0 and key == ord('F'):
                    self.begin_get_continuing_key(self.shortcuts_begin(lambda nd: nd.focus()), key, mod)
                elif mod == 0 and key == ord('G'):
                    def l(nd):
                        nd.move_to_workspace(self.focused_master, self.focused_slave)
                        self.load_i3_tree()
                        self.cmd_msg("OK")
                    self.begin_get_continuing_key(self.shortcuts_begin(l), key, mod)
                elif mod == 0 and key == ord('M'):
                    def l(nd_from):
                        nd_from.marked = QColor(255,0,0);
                        nd_from.redraw()
                        def end():
                            nd_from.marked = None
                            nd_from.redraw()
                        def ll(nd_to):
                            nd_to.marked = QColor(0,255,0);
                            nd_to.redraw()
                            def lll(key, mod):
                                nd_to.marked = None
                                nd_to.redraw()
                                end()
                                if key is None:
                                    return
                                elif mod == 0 and key == ord('N'):
                                    nd_from.move_after(nd_to)
                                elif mod == 0 and key == ord('M'):
                                    nd_from.expand_after(nd_to)
                                elif mod == 0 and key == ord('I'):
                                    nd_from.move_before(nd_to)
                                elif mod == 0 and key == ord('O'):
                                    nd_from.expand_before(nd_to)
                                elif mod in [0, SHIFT] and key == ord('H'):
                                    nd_from.move_to_new_container_with(nd_to, "splith", before=mod==SHIFT)
                                elif mod in [0, SHIFT] and key == ord('V'):
                                    nd_from.move_to_new_container_with(nd_to, "splitv", before=mod==SHIFT)
                                elif mod in [0, SHIFT] and key == ord('T'):
                                    nd_from.move_to_new_container_with(nd_to, "tabbed", before=mod==SHIFT)
                                elif mod in [0, SHIFT] and key == ord('S'):
                                    nd_from.move_to_new_container_with(nd_to, "stacked", before=mod==SHIFT)
                                elif mod in [0, SHIFT] and key == ord('J'):
                                    nd_from.move_to_new_container_with(nd_to, "splith", before=mod==SHIFT, expand=True)
                                elif mod in [0, SHIFT] and key == ord('B'):
                                    nd_from.move_to_new_container_with(nd_to, "splitv", before=mod==SHIFT, expand=True)
                                elif mod in [0, SHIFT] and key == ord('Y'):
                                    nd_from.move_to_new_container_with(nd_to, "tabbed", before=mod==SHIFT, expand=True)
                                elif mod in [0, SHIFT] and key == ord('D'):
                                    nd_from.move_to_new_container_with(nd_to, "stacked", before=mod==SHIFT, expand=True)
                                self.load_i3_tree()
                                self.cmd_msg("OK")
                            return lll
                        def filter(nd):
                            while nd is not None:
                                if nd == nd_from:
                                    return False
                                nd = nd.parentWidget()
                            return True
                        return self.shortcuts_begin(ll, fail=end, filter=filter)
                    self.begin_get_continuing_key(self.shortcuts_begin(l), key, mod)
                elif mod == 0 and key == ord('R'):  # Undocumented
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
                elif mod == 0 and key == ESCAPE:  # ESCAPE
                    with shared.lock.read:
                        w = get_workspace()
                    shared.i3_cmd(f'workspace {workspace(*w)}')
                elif mod == 0 and key == 16777220:  # ENTER
                    shared.i3_cmd(f'workspace {workspace(self.focused_master, self.focused_slave)}')

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
            try:
                if app.focusWidget() == self._find_input:
                    keyPressEvent_find(key, mod)
                else:
                    keyPressEvent_main(key, mod)
            except I3CmdException as e:
                self.end_get_continuing_key()
                self.cmd_msg(e.error, QColor(255, 100, 100))
                traceback.print_exc()
                m_win.load_i3_tree()

        def show_help(self):
            self._help_window.show()

        def move_to_gui_workspace(self):
            print(shared.i3_cmd(f'[id={int(self.winId())}] move container to workspace 0'))

    m_win = MainWindow()
    m_win.show()
    m_win.move_to_gui_workspace()

    with shared.lock:
        load_workspaces()

    app.exec_()
