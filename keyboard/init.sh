#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 2
is_sysconfig=true
install_begin
clean_userinstall

confln cz /usr/share/X11/xkb/symbols/cz c

confln keyboard.conf /etc/X11/xorg.conf.d/00-keyboard.conf

install_ok
