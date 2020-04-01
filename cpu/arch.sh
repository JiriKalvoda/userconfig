#!/bin/bash
cd "$(dirname "$0")"
if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
g++ ./cpuF.c -o /usr/bin/cpuF
chmod u+s /usr/bin/cpuF
cp ./cpuFGUI.sh  /usr/bin/cpuFGUI
chmod o+x /usr/bin/cpuFGUI
if [ "$1" == no ];
then
	exit;
fi
sudo pacman -S cpupower


