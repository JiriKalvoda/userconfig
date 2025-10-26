#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 1
install_begin

confln toggle-border ~/.config/i3/i3-toggle-border
confln kill ~/.config/i3/i3-kill
confln i3status.conf ~/.config/i3/
confln i3csstatus.conf ~/.config/i3/ c
cat >~/.xinitrc <<EOF
exec i3
EOF
r g++ status.cpp -o ~/.config/i3/status.out

r ../git-clupdate git@gitlab.kam.mff.cuni.cz:jirikalvoda/i3-woman.git build_git_i3-woman
r -b "cd build_git_i3-woman; make"
confln build_git_i3-woman/daemon.py ~/bin/i3-woman-daemon
confln build_git_i3-woman/client ~/bin/i3-woman

r ../git-clupdate git@gitlab.kam.mff.cuni.cz:jirikalvoda/i3csstatus.git build_git_i3csstatus
r -b "cd build_git_i3csstatus ; dotnet build --no-self-contained --configuration Release"
confln build_git_i3csstatus/bin/Release/net9.0/i3csstatus ~/bin/

r -c ./config-gen/init.sh

install_ok
