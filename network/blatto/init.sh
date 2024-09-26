#!/bin/bash
cd "$(dirname "$0")"
. ../../userconfig-lib.sh
version 1
is_sysconfig=true
install_begin
clean_userinstall

confln blatto.config-defaults /etc/net/ r

if ! [[ -f /etc/net/blatto.config ]]
then
	confln blatto.config-init /etc/net/blatto.config cr
	r -Pc vim /etc/net/blatto.config
fi

while true
do
	bash <<AMEN
	set -eu
	. /etc/net/blatto.config
	echo \$blatto_username \$blatto_user \$blatto_user_id \$blatto_device_id
AMEN
	if [[ $? != 0 ]]
	then
		echo error in config
		r -Pc vim /etc/net/blatto.config
	else
		break
	fi
done



if $(bash -c '. /etc/net/blatto.config; echo $blatto_wg')
then
	r ./wg-blatto-init
	confln wg-blatto /etc/net/ r
	confln wg-blatto-fix-egypt /etc/net/ r
fi

confln untr-bl /etc/net/ r

confln scripts/con-sm /etc/net/ r
confln scripts/con-e /etc/net/ r

install_ok
