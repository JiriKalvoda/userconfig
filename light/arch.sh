#!/bin/bash
cd "$(dirname "$0")"
if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
#apt install notify-osd
g++ ./light.c -o /usr/bin/light
chmod u+s /usr/bin/light
g++ ./lightInfo.c -o /usr/bin/lightInfo
chmod u+s /usr/bin/lightInfo
cp ./lightGUI.sh  /usr/bin/lightGUI
chmod o+x /usr/bin/lightGUI


