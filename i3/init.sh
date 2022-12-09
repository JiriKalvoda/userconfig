#!/bin/bash
../userconfig-lib ..

confln toggle-border ~/.config/i3/i3-toggle-border
confln kill ~/.config/i3/i3-kill
confln i3status.conf ~/.config/i3/
confln i3csstatus.conf ~/.config/i3/
cat >~/.xinitrc <<EOF
exec i3
EOF
g++ status.cpp -o ~/.config/i3/status.out

../git-clupdate git@gitlab.kam.mff.cuni.cz:jirikalvoda/i3-woman.git build_git_i3-woman

./config-gen/init.sh
