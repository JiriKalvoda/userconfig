#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

echo -e "\e[31mROOT REQUIRE\e[0m"

if not grep  "BETTER XDG-OPEN" /usr/bin/xdg-open
then
	mv /usr/bin/xdg-open /usr/bin/xdg-open-real
fi

confln better-xdg-open.py /usr/bin/better-xdg-open c
confln better-xdg-open.py /usr/bin/xdg-open c
confln open-desktop-file /usr/bin/ c

install_ok
