#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 2
is_sysconfig=true
install_begin

confln podman-compose@.service /etc/systemd/system/ c


install_ok
