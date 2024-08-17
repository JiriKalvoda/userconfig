#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

version 1
install_begin

. $USERCONFIG_ROOT/blach/import_blach.sh

tmpf=$(mktemp)
r -b "$blach/ssh/config-gen.py > $tmpf"
confln $tmpf ~/.ssh/config c
rm $tmpf

install_ok
