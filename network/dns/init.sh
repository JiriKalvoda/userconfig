#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 2
install_begin

confln resolv.conf /etc/ c
confln resolvconf.conf /etc/ cr
confln unbound.conf /etc/unbound/ c

r unbound-control-setup

install_ok
