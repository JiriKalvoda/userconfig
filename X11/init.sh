#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln xorg.conf /etc/X11/
confln 10-reverse-touchapd.conf /etc/X11/xorg.conf.d/ d

install_ok
