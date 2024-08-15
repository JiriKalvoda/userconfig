#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 3
is_sysconfig=true
install_begin
clean_userinstall


confln resolv.conf /etc/ c
confln resolvconf.conf /etc/ cr
confln unbound.conf /etc/unbound/ c

r unbound-control-setup

install_ok
