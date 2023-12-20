#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln userconfig_state_server.sh ~/bin/ E

install_ok
