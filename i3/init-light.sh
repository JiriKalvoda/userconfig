#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln toggle-border ~/.config/i3/i3-toggle-border
confln kill ~/.config/i3/i3-kill
confln i3status.conf ~/.config/i3/
cat >~/.xinitrc <<EOF
exec i3
EOF
r g++ status.cpp -o ~/.config/i3/status.out

install_ok
