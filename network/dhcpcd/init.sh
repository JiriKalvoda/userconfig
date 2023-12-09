#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
install_begin

confln dhcpcd-custom@.service /lib/systemd/system/ cr

install_ok
