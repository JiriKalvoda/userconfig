#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln toggle-border ~/.config/i3/i3-toggle-border
confln kill ~/.config/i3/i3-kill
confln i3status.conf ~/.config/i3/
confln i3csstatus.conf ~/.config/i3/
cat >~/.xinitrc <<EOF
exec i3
EOF
r g++ status.cpp -o ~/.config/i3/status.out

r ../git-clupdate git@gitlab.kam.mff.cuni.cz:jirikalvoda/i3-woman.git build_git_i3-woman

r ../git-clupdate git@gitlab.kam.mff.cuni.cz:jirikalvoda/i3csstatus.git build_git_i3csstatus
r -b "cd build_git_i3csstatus ; dotnet build --no-self-contained --configuration Release"
confln build_git_i3csstatus/bin/Release/net7.0/i3csstatus ~/bin/

r ./config-gen/init.sh

install_ok
