#!/usr/bin/python

# BETTER XDG-OPEN

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import subprocess
import shutil

import sys, os

import re

def is_file_url_or_path(arg):
    if re.search("^file://", arg):
        return True
    if re.search('^[a-zA-Z][a-zA-Z0-9+\.\-]*:', arg):
        return False
    return True

def file_url_to_path(arg):
    if re.search('^file://(localhost)?/', arg):
        r = subprocess.run(['bash', '/dev/stdin', arg], stdout=subprocess.PIPE, encoding='utf-8', check=True, input="""
file="$1"
file=${file#file://localhost}
file=${file#file://}
file=${file%%#*}
file=$(echo "$file" | sed -r 's/\?.*$//')
printf=printf
if [ -x /usr/bin/printf ]; then
    printf=/usr/bin/printf
fi
file=$($printf "$(echo "$file" | sed -e 's@%\([a-f0-9A-F]\{2\}\)@\\x\1@g')")
echo "$file"
        """)
        return r.stdout.strip()
    return arg

arg = sys.argv[1]
script_dir = "/".join(sys.argv[0].split("/")[:-1])
file = file_url_to_path(arg) if is_file_url_or_path(arg) else None
absolute_file = file
if absolute_file and absolute_file[0] != '/':
    absolute_file = os.getcwd() + "/" + absolute_file

print("FILE", file)
if file is not None:
    r = subprocess.run(['xdg-mime', 'query', 'filetype', file], stdout=subprocess.PIPE, encoding='utf-8')
    filetype = r.stdout.strip() if not r.returncode else None

else:
    scheme = re.search('^([a-zA-Z][a-zA-Z0-9+\.\-]*):', arg).group(1)
    filetype = f"x-scheme-handler/{scheme}"

if filetype is None:
    xdg_default = None
else:
    r = subprocess.run(['xdg-mime', 'query', 'default', filetype], stdout=subprocess.PIPE, encoding='utf-8')
    xdg_default = r.stdout.strip() if not r.returncode else None


def end():
    m_win.hide()

def terminal_cmd(terminal=True):
    if terminal:
        return ["terminal", "-e"]
    else:
        return []

def shell_escape(*args):
    return " ".join("'" + i.replace("'", "'\"'\"'") + "'" for i in args)

def is_vm():
    return m_win._vm.isChecked()
def vm_run(cmd, gui=False):
    r = subprocess.run(["vm", "extended_name", m_win._vm_name.text()], stdout=subprocess.PIPE, encoding='utf-8')
    vm_id, vm_user = r.stdout.strip().split("\n")
    if gui:
        p = subprocess.run(["vm", "vncapp", vm_user+'@'+vm_id, shell_escape(*cmd)])
    else:
        p = subprocess.run([*terminal_cmd(), "vm", "ssh", vm_user+'@'+vm_id, shell_escape(*cmd)])



def open_xdg_open(terminal=False):
    end()
    if is_vm():
        vm_run(["xdg-open", arg], gui=not terminal)
        exit(0)
    else:
        xdg_open_bin = shutil.which("xdg-open-real") or shutil.which("xdg-open") 
        p = subprocess.run([*terminal_cmd(terminal), xdg_open_bin, arg])
        exit(p.returncode)

def open_desktop(desktop_app=None, terminal=False):
    end()
    if is_vm():
        vm_run(["open-desktop-file", desktop_app or xdg_default, arg], gui=not terminal)
        exit(0)
    else:
        p = subprocess.run([*terminal_cmd(terminal), script_dir+"/open-desktop-file", desktop_app or xdg_default, arg])
        exit(p.returncode)

def open_vim():
    end()
    vim_bin = shutil.which("nvim") or shutil.which("vim") 
    p = subprocess.run([*terminal_cmd(), vim_bin, arg])
    exit(p.returncode)

def open_browser(window=False, anonim=False, session=False):
    import tempfile
    end()
    anonim_arg = ["--incognito"] if anonim else []
    window_arg = ["--new‐window"] if window else []
    session_arg = ["--user-data-dir="+tempfile.mkdtemp()] if session else []
    p = subprocess.run(["chromium", *anonim_arg, *window_arg, *session_arg, arg])
    exit(p.returncode)


def copy(arg, do_exit=True):
    p = subprocess.run(["xclip", "-i", "-selection", "clipboard"], encoding='utf-8', input=arg)
    if do_exit:
        exit(p.returncode)
    return p


qtoverride = lambda x: x  # only documentation of code

copyed_label = None

class BetterLabel(QLabel):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.setTextFormat(Qt.PlainText)
        self.setText(text)
        self.setAutoFillBackground(True)

    def mousePressEvent(self, event):
        global copyed_label
        copy(self.text(), do_exit=False)
        self.setStyleSheet("color: #990000")
        if copyed_label:
            copyed_label.setStyleSheet("color: #000000")
        copyed_label = self



class MainWindow(QWidget):
    def new_button(self, name, text):
        b = QPushButton(self)
        b.setText(text)
        b.clicked.connect(getattr(self, name+'_clicked'))
        return b


    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("better xdg-open")

        self._lay = QVBoxLayout(self)

        self._arg = BetterLabel(self, arg)
        font = self.font()
        font.setPointSize(20)
        self._arg.setFont(font)
        self._lay.addWidget(self._arg)

        self._wd = BetterLabel(self, os.getcwd())
        self._lay.addWidget(self._wd)

        if filetype is not None:
            self._filetype = BetterLabel(self, filetype)
            self._lay.addWidget(self._filetype)

        if xdg_default:
            self._xdg_default = BetterLabel(self, xdg_default)
            self._lay.addWidget(self._xdg_default)

        
        self._lay.addWidget(self.new_button('_copy', "&copy"))
        self._lay.addWidget(self.new_button('_vim', "&vim"))

        self._vm = QGroupBox("&Virtual machine");
        self._vm_lay = QHBoxLayout()
        self._vm.setLayout(self._vm_lay)
        self._vm.setCheckable(True)
        self._vm.setChecked(False)
        self._vm_name = QLineEdit(self._vm)
        self._vm_name.setText("+")
        self._vm_lay.addWidget(self._vm_name)
        self._lay.addWidget(self._vm)
        
        self._lay_browser = QHBoxLayout()
        self._lay_browser.addWidget(self.new_button('_browser', "chromium &tab"))
        self._lay_browser.addWidget(self.new_button('_browser_w', "chromium &window"))
        self._lay.addLayout(self._lay_browser)

        self._lay_browser2 = QHBoxLayout()
        self._lay_browser2.addWidget(self.new_button('_browser_anonim', "chromium &anonim"))
        self._lay_browser2.addWidget(self.new_button('_browser_session', "chromium &session"))
        self._lay.addLayout(self._lay_browser2)

        self._lay_open = QHBoxLayout()
        self._lay_open.addWidget(self.new_button('_open', "&open"))
        self._lay_open.addWidget(self.new_button('_open_t', "&Open &terminal"))
        self._lay.addLayout(self._lay_open)

        self._lay_xdg_open = QHBoxLayout()
        self._lay_xdg_open.addWidget(self.new_button('_xdg_open', "&xdg-open"))
        self._lay_xdg_open.addWidget(self.new_button('_xdg_open_t', "&Xdg-open terminal"))
        self._lay.addLayout(self._lay_xdg_open)

        self.setLayout(self._lay)


    @pyqtSlot(bool)
    def _browser_clicked(self, x):
        open_browser()
    @pyqtSlot(bool)
    def _browser_w_clicked(self, x):
        open_browser(window=True)
    @pyqtSlot(bool)
    def _browser_anonim_clicked(self, x):
        open_browser(anonim=True)
    @pyqtSlot(bool)
    def _browser_session_clicked(self, x):
        open_browser(session=True)

    @pyqtSlot(bool)
    def _copy_clicked(self, x):
        copy(absolute_file or arg)

    @pyqtSlot(bool)
    def _vim_clicked(self, x):
        open_vim()

    @pyqtSlot(bool)
    def _xdg_open_clicked(self, x):
        open_xdg_open()
    @pyqtSlot(bool)
    def _xdg_open_t_clicked(self, x):
        open_xdg_open(terminal=True)

    @pyqtSlot(bool)
    def _open_clicked(self, x):
        open_desktop()
    @pyqtSlot(bool)
    def _open_t_clicked(self, x):
        open_desktop(terminal=True)

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
        ESCAPE = 16777216;
        ENTER = 16777220;

        print(event, type(event), event.text(), event.key(), int(event.modifiers()))
        mod = int(event.modifiers())
        key = int(event.key())

        event.accept()

        if key == ESCAPE:
            exit(0)
        if key == ENTER:
            open_xdg_open()





app = QApplication(sys.argv)

m_win = MainWindow()
m_win.show()


app.exec_()
