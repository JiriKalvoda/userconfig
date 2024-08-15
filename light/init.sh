#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
is_sysconfig=true
install_begin
clean_userinstall


confln config-default.h config.h c

r g++ ./light.c -o /usr/bin/light
r chmod u+s /usr/bin/light
r g++ ./lightInfo.c -o /usr/bin/lightInfo
r chmod u+s /usr/bin/lightInfo
confln ./lightGUI.sh  /usr/bin/ E
r chmod o+x /usr/bin/lightGUI

install_ok
