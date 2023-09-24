#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln i3.py ~/bin/keymap-i3
confln tex.py ~/bin/keymap-tex
confln doc.sh ~/bin/keymap-doc
confln cpp-keyboard.py ~/bin/keymap-cpp-keyboard

install_ok
