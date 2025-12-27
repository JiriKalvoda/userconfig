#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln X11-touchpad-speed.conf /etc/X11/xorg.conf.d/71-touchpad-speed.conf r

install_ok
