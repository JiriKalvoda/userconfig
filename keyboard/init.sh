#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
need_root
install_begin

confln cz /usr/share/X11/xkb/symbols/cz c

confln keyboard.conf /etc/X11/xorg.conf.d/00-keyboard.conf cr

install_ok
