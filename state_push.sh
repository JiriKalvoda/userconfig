#!/bin/bash
. ../userconfig-lib.sh

install_config_load

if [[ $ic_push == "" ]]
then
	echo "${Red}No push hook for state dir!$None"
	exit 1
else
	cd $USERCONFIG_ROOT/state || err cd faild
	r -b "tar --create --to-stdout . | $ic_push  bin/userconfig_state_server $ic_name"
fi
