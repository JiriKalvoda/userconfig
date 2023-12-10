#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln htoprc ~/.config/htop/ c

install_ok
