#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln tripscope-sync.service /etc/systemd/system/
r systemctl enable tripscope-sync

install_ok
