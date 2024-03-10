#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 1
install_begin

confln alacritty.toml ~/.config/alacritty/
confln  spawn-alacritty-cwd ~/.config/alacritty/

install_ok
