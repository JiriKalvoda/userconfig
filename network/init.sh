#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 14
is_sysconfig=true
install_begin
clean_userinstall

confln net-config@.service /lib/systemd/system/ cr
confln set-wifi@.service /lib/systemd/system/ cr
confln send-broadcast@.service /lib/systemd/system/ cr
confln dhcpcd-custom@.service /lib/systemd/system/ cr

confln jk-net.rules /etc/udev/rules.d/ r

confln iwd.conf /etc/iwd/main.conf

confln ip-man /usr/bin/
init-service ip-man root "/usr/bin/ip-man server" "" ""

h=$(hostname)
for i in $h/scripts/*;
do
	if [ -f "$i" ]
	then
		confln "$i" /etc/net/ r
	fi
done

if [ -f $h/dhcpcd.conf ]
then
	confln $h/dhcpcd.conf /etc/
else
	confln dhcpcd.conf /etc/
fi

confln dhcpcd.enter-hook-defaults /etc/ r
confln dhcpcd.enter-hook-defs /etc/ r
if [ -f $h/dhcpcd.enter-hook ]
then
	confln $h/dhcpcd.enter-hook /etc/ r
else
	confln dhcpcd.enter-hook /etc/ r
fi

r udevadm control --reload-rules
r udevadm trigger

r -c git_clupdate https://codeberg.org/regnarg/cdwifi-autologin.git build_git_cdwifi-autologin
confln build_git_cdwifi-autologin/cdwifi-autologin.sh /usr/bin/ E
confln cdwifi-autologin.service /lib/systemd/system/ r

confln blatto-daemon.py /usr/bin/net-blatto-daemon
init-service net-blatto-daemon root /usr/bin/net-blatto-daemon "" "ExecReload=/bin/kill -HUP \$MAINPID"

confln namespaces /etc/net/ r


gcc change_ns.c -o /usr/bin/net_direct -DTARGET_NAMESPACE=\"2direct\"
r chmod 4755 /usr/bin/net_direct
for x in 2{,untr-}bl{,-mul,-awn,-mn} 2untr
do
	gcc change_ns.c -o /usr/bin/net_$x -DTARGET_NAMESPACE=\"$x\"
	r chmod 4755 /usr/bin/net_$x
done



install_ok
