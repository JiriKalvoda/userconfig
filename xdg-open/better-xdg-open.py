#!/usr/bin/python

# BETTER XDG-OPEN

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import subprocess
import shutil

import sys, os

import re
import tempfile

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


assert len(sys.argv) <= 2
if len(sys.argv) == 2:
    arg = sys.argv[1]
else:
    arg_tmp_file = tempfile.NamedTemporaryFile()
    subprocess.run(["cat"], stdout=arg_tmp_file)
    arg = arg_tmp_file.name

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

with open("/usr/share/applications/mimeinfo.cache") as f:
    x = [i.strip() for i in f.read().split('\n') if i.startswith(filetype+"=")]
    assert len(x) <= 1
    possible_apps = list(x[0][len(filetype)+1:].split(';')) if len(x) else []

print(possible_apps)


def end():
    m_win.hide()

def terminal_cmd(terminal=True):
    if terminal:
        return ["terminal", "-e"]
    else:
        return []

def shell_escape(*args):
    return " ".join("'" + i.replace("'", "'\"'\"'") + "'" for i in args)
def shell_escape_if_list(a):
    if isinstance(a, str):
        return a
    return shell_escape(*a)


def path_to_filename(arg):
    if not is_file_url_or_path(arg):
        return arg
    arg = file_url_to_path(arg)
    return arg.split('/')[-1]

def is_vm():
    return m_win._vm.isChecked()
def vm_run(cmd, gui=False):
    cmd = shell_escape_if_list(cmd)
    r = subprocess.run(["vm", "extended_name", m_win._vm_name.text()], stdout=subprocess.PIPE, encoding='utf-8')
    vm_id, vm_user = r.stdout.strip().split("\n")
    if is_file_url_or_path(arg):
        r = subprocess.run(["vm", "sshfs", vm_id, "--user", vm_user], encoding='utf-8')
        r = subprocess.run(["vm", "sshfs_mountdir", vm_id, "--user", vm_user], stdout=subprocess.PIPE, encoding='utf-8')
        mountdir = r.stdout.strip()

        path = file_url_to_path(arg)
        filename = path.split('/')[-1]

        tmp_dir = tempfile.mkdtemp(prefix="xdg-open-", dir=mountdir+'~')
        tmp_dir_name = tmp_dir.split('/')[-1]
        shutil.copy(file, tmp_dir+"/"+filename)
        if gui:
            p = subprocess.run(["vm", "vncapp", vm_user+'@'+vm_id, "--", f"cd {tmp_dir_name}; {cmd}"])
        else:
            p = subprocess.run([*terminal_cmd(), "vm", "ssh", vm_user+'@'+vm_id, "--", "-t", "--", f"cd {tmp_dir_name}; {cmd}"])
    else:
        if gui:
            p = subprocess.run(["vm", "vncapp", vm_user+'@'+vm_id, "--", cmd])
        else:
            p = subprocess.run([*terminal_cmd(), "vm", "ssh", vm_user+'@'+vm_id, "--", "-t", "--", cmd])



def open_xdg_open(terminal=False):
    end()
    if is_vm():
        vm_run(["xdg-open", path_to_filename(arg)], gui=not terminal)
        exit(0)
    else:
        xdg_open_bin = shutil.which("xdg-open-real") or shutil.which("xdg-open") 
        p = subprocess.run([*terminal_cmd(terminal), xdg_open_bin, path_to_filename(arg)])
        exit(p.returncode)

def get_app():
    cur_it = m_win._app_list.currentItem()
    if cur_it is not None:
        return cur_it.data(42)
    else:
        return xdg_default

def open_desktop(desktop_app=None, terminal=False):
    if desktop_app is None:
        desktop_app = get_app()
    end()
    if is_vm():
        vm_run(["open-desktop-file", desktop_app or xdg_default, path_to_filename(arg)], gui=not terminal)
        exit(0)
    else:
        p = subprocess.run([*terminal_cmd(terminal), script_dir+"/open-desktop-file", desktop_app or xdg_default, arg])
        exit(p.returncode)

def set_default():
    subprocess.run(["xdg-mime", "default", get_app(), filetype], check=True)

def open_bash():
    end()
    cmd =f"""
export f={shell_escape(arg)}
export filetype={shell_escape(filetype)}
export default={shell_escape(xdg_default)}
echo XDG-OPEN SHELL
echo f="$f"
echo filetype="$filetype"
echo default="$default"
exec bash"""
    if is_vm():
        p = vm_run(cmd, gui=False)
        exit(0)
    else:
        p = subprocess.run([*terminal_cmd(), "bash", "-c", cmd])
        exit(p.returncode)

def open_vim():
    end()
    if is_vm():
        p = vm_run(["vim", path_to_filename(arg)], gui=False)
        exit(0)
    else:
        vim_bin = shutil.which("nvim") or shutil.which("vim") 
        p = subprocess.run([*terminal_cmd(), vim_bin, arg])
        exit(p.returncode)

def open_browser(window=False, incognito=False, session=False):
    import tempfile
    end()
    incognito_arg = ["--incognito"] if incognito else []
    window_arg = ["--new-window"] if window else []
    session_arg = ["--user-data-dir="+tempfile.mkdtemp()] if session else []
    if is_vm():
        p = vm_run(["chromium", *incognito_arg, *window_arg, *session_arg, path_to_filename(arg)], gui=True)
        exit(0)
    else:
        p = subprocess.run(["chromium", *incognito_arg, *window_arg, *session_arg, arg])
        exit(p.returncode)


def copy(arg, do_exit=True):
    p = subprocess.run(["xclip", "-i", "-selection", "clipboard"], encoding='utf-8', input=arg)
    if do_exit:
        exit(p.returncode)
    return p

def back_default():
    m_win._app_list.setCurrentItem(None)


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
        if copyed_label:
            copyed_label.setStyleSheet("color: #000000")
        self.setStyleSheet("color: #990000")
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
        self._lay.addWidget(self.new_button('_vim', "&edit with vim"))
        self._lay.addWidget(self.new_button('_bash', "&bash"))
        
        self._lay_browser = QHBoxLayout()
        self._lay_browser.addWidget(self.new_button('_browser', "chromium &t&a&b"))
        self._lay_browser.addWidget(self.new_button('_browser_w', "chromium &window"))
        self._lay.addLayout(self._lay_browser)

        self._lay_browser2 = QHBoxLayout()
        self._lay_browser2.addWidget(self.new_button('_browser_incognito', "chromium &incognito"))
        self._lay_browser2.addWidget(self.new_button('_browser_session', "chromium &session"))
        self._lay.addLayout(self._lay_browser2)

        self._vm = QGroupBox("&Virtual machine");
        self._vm_lay = QHBoxLayout()
        self._vm.setLayout(self._vm_lay)
        self._vm.setCheckable(True)
        self._vm.setChecked(False)
        self._vm_name_lay = QHBoxLayout()
        self._vm_name_title = QLabel("<u>n</u>ame:")
        self._vm_name_lay.addWidget(self._vm_name_title)
        self._vm_name = QLineEdit(self._vm)
        self._vm_name.setText("+")
        self._vm_name_lay.addWidget(self._vm_name)
        self._vm_lay.addLayout(self._vm_name_lay)
        self._lay.addWidget(self._vm)

        self._default_lay = QHBoxLayout()
        self._default_lay.addWidget(self.new_button('_back_default', "&default: "+xdg_default))
        self._default_lay.addWidget(self.new_button('_set_default', "&use as default"))
        self._lay.addLayout(self._default_lay)

        self._app_list = QListWidget()
        for i in possible_apps:
            item = QListWidgetItem(i, self._app_list);
            item.setData(42, i)
            if i == xdg_default:
               self._app_list.setCurrentItem(item)
        self._lay.addWidget(self._app_list)

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
    def _browser_incognito_clicked(self, x):
        open_browser(incognito=True)
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
    def _bash_clicked(self, x):
        open_bash()

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

    @pyqtSlot(bool)
    def _back_default_clicked(self, x):
        back_default()
    @pyqtSlot(bool)
    def _set_default_clicked(self, x):
        set_default()

    @qtoverride
    def focusNextPrevChild(self, next):
        return False

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
        TAB = 16777217;

        print(event, type(event), event.text(), event.key(), int(event.modifiers()))
        mod = int(event.modifiers())
        key = int(event.key())

        print(app.focusWidget())

        if app.focusWidget() in [self._vm_name, self._app_list]:
            if key in [ESCAPE, ENTER]:
                self.setFocus()
            return



        event.accept()

        if key == ESCAPE:
            exit(0)
        if key in [ENTER, ord("O")]:
            open_desktop(terminal=(mod == SHIFT))
        if key == ord("X"):
            open_xdg_open(terminal=(mod == SHIFT))
        if key == ord("T"):
            open_desktop(terminal=True)
        if key == ord("E"):
            open_vim()
        if key == ord("B"):
            open_bash()
        if key == ord("C"):
            copy(arg)
        if key == TAB:
            open_browser()
        if key == ord("W"):
            open_browser(window=True)
        if key == ord("I"):
            open_browser(incognito=True)
        if key == ord("S"):
            open_browser(session=True)

        if key == ord("V"):
            self._vm.setChecked(not self._vm.isChecked())
        if key == ord("N"):
            self._vm.setChecked(True)
            self._vm_name.setFocus()
            self._vm_name.selectAll()
        if key == ord("U"):
            set_default()
        if key == ord("D"):
            back_default()
            

app = QApplication(sys.argv)

m_win = MainWindow()
m_win.show()


app.exec_()
