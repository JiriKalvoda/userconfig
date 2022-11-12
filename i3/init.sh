#!/bin/bash
cd "$(dirname "$0")"

confln toggle-border ~/.config/i3/i3-toggle-border
confln kill ~/.config/i3/i3-kill
confln i3status.conf ~/.config/i3/
confln i3csstatus.conf ~/.config/i3/
chmod o+x ~/.config/i3/i3-*
cat >~/.xinitrc <<EOF
exec i3
EOF
g++ status.cpp -o ~/.config/i3/status.out

