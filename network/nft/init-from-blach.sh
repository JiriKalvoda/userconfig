#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh

is_sysconfig=true
version 1
install_begin

. $USERCONFIG_ROOT/blach/import_blach.sh

tmpf=$(mktemp)
r -b "$blach/nftables/gen_jk_clients.py > $tmpf"
confln $tmpf /etc/nftables.conf c
rm $tmpf
r nft -f /etc/nftables.conf
r systemctl enable nftables

confln sysctl.conf /etc/sysctl.d/10-net.conf r
confln  nftbles.service.sysctl.conf /etc/systemd/system/nftables.service.d/sysctl.conf


install_ok
