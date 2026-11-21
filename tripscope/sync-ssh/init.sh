#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln sshd.conf /etc/ssh/sshd_config.d/tripscope-sync.conf
confln tripscope-sync-keys /usr/local/bin/

install_ok
