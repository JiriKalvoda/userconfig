#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln gitconfig ~/.gitconfig

install_ok
