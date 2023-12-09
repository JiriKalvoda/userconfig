#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
install_begin

confln conntrack_hack_daemon.py /bin/ E

init-service conntrack_hack root conntrack_hack_daemon

install_ok
