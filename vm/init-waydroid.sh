#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln waydroid-run.py ~/bin/ E

install_ok
