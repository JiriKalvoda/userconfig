#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln snapshoter ~/bin/
confln "snapshoter.devices-$(hostname)" ~/snapshoter.devices

install_ok
