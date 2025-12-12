#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln run.py ~/bin/label-maker

install_ok
