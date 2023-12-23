#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
need_root
install_begin

confln config-default.h config.h c

r g++ ./light.c -o /usr/bin/light
r chmod u+s /usr/bin/light
r g++ ./lightInfo.c -o /usr/bin/lightInfo
r chmod u+s /usr/bin/lightInfo
r cp ./lightGUI.sh  /usr/bin/lightGUI
r chmod o+x /usr/bin/lightGUI

install_ok
