#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 8
need_root
install_begin

confln net-config@.service /lib/systemd/system/ cr
confln set-wifi@.service /lib/systemd/system/ cr
confln send-broadcast@.service /lib/systemd/system/ cr
confln dhcpcd-custom@.service /lib/systemd/system/ cr

confln jk-net.rules /etc/udev/rules.d/ cr

confln iwd.conf /etc/iwd/main.conf c

h=$(hostname)
for i in $h/scripts/*;
do
	if [ -f "$i" ]
	then
		confln "$i" /etc/net/ cr
	fi
done

[ -f $h/dhcpcd.conf ] && confln $h/dhcpcd.conf /etc/ cr
[ -f $h/dhcpcd.enter-hook ] && confln $h/dhcpcd.enter-hook /etc/ cr

r udevadm control --reload-rules
r udevadm trigger

r -c git_clupdate https://codeberg.org/regnarg/cdwifi-autologin.git build_git_cdwifi-autologin
confln build_git_cdwifi-autologin/cdwifi-autologin.sh /usr/bin/ cE
confln cdwifi-autologin.service /lib/systemd/system/ cr

confln blatto-daemon.py /usr/bin/net-blatto-daemon c
init-service net-blatto-daemon root /usr/bin/net-blatto-daemon "" "ExecReload=/bin/kill -HUP \$MAINPID"

install_ok
