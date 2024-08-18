#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 0
is_sysconfig=true
install_begin

confln sshd_config /etc/ssh/

install_ok
