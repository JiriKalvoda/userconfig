#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 1
install_begin

confln status.py /usr/bin/snapshoter-status c
confln profile.sh /etc/profile.d/snapshoter.sh cd

install_ok
