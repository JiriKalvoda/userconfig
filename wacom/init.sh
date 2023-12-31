#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln wacom-config ~/bin/
r gcc wacom-daemon2.c -o ~/bin/wacom-daemon -lxdo

install_ok
