#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln alacritty.toml ~/.config/alacritty/
confln  spawn-alacritty-cwd ~/.config/alacritty/

install_ok
