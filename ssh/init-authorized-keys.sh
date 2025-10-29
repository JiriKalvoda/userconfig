#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

source=authorized_keys

if [[ $1 != "" ]]
then
	source=authorized_keys_$1
fi



version 3
install_begin

[[ -f ~/.ssh/authorized_keys ]] && cat ~/.ssh/authorized_keys > $state_run_dir/files/old_authorized_keys

confln "$source" ~/.ssh/authorized_keys -c
cat ~/.ssh/authorized_keys > $state_run_dir/files/authorized_keys

echo
r sha256sum ~/.ssh/authorized_keys
echo

install_ok
