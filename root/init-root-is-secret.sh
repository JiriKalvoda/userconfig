#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln ~/.ssh/id_ed25519_secret ~/.config/root_key

install_ok
