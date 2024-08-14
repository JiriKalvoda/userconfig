#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

install_begin

. $USERCONFIG_ROOT/blach/import_blach.sh

tmpf=$(mktemp)
$blach/ssh/config-gen.py > $tmpf
confln $tmpf ~/.ssh/config c
rm $tmpf

install_ok
