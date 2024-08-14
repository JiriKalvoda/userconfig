#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
is_sysconfig=true
version 0
install_begin

r ../git-clupdate git@git.blatto.eu:blatto/blach.git /etc/blach
confln me.py /etc/blach/blach/
r -b "cd /etc/blach && pip install -e . --break-system-packages"

install_ok
