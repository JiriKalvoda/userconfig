#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln X11-touchpad-scroll.conf /etc/X11/xorg.conf.d/70-touchpad-scrool.conf r

install_ok
