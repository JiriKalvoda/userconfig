#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln tripscope-data.service /etc/systemd/system/
r systemctl enable tripscope-data
confln sshd.conf /etc/ssh/sshd_config.d/tripscope-data.conf
confln tripscope-data /usr/local/bin/

install_ok
