#!/bin/bash
cd "$(dirname "$0")"
if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
g++ ./volumeInfo.c -o /usr/bin/volumeInfo
chmod u+s /usr/bin/volumeInfo
cp ./volumeGUI.sh  /usr/bin/volumeGUI
chmod o+x /usr/bin/volumeGUI


