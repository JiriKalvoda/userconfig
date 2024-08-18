#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh

is_sysconfig=true
install_begin

. $USERCONFIG_ROOT/blach/import_blach.sh

tmpf=$(mktemp)
r -b "$blach/nftables/gen_jk_clients.py > $tmpf"
confln $tmpf /etc/nftables.conf c
r nft -f /etc/nftables.conf
rm $tmpf

install_ok
