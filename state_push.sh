#!/bin/bash
cd "$(dirname "$0")"
. userconfig-lib.sh

install_config_load

if [[ $ic_push == "" ]]
then
	echo -e "${Red}No push hook for state dir!$None"
	exit 0
else
	cd $USERCONFIG_ROOT/state || err cd faild
	r -b "tar --create --to-stdout . | $ic_push  bin/userconfig_state_server $ic_name"
fi
