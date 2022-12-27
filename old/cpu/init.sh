#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"

g++ ./cpuF.c -o /usr/bin/cpuF
chmod u+s /usr/bin/cpuF
cp ./cpuFGUI.sh  /usr/bin/cpuFGUI
chmod o+x /usr/bin/cpuFGUI
if [ "$1" == "arch" ];
then
	pacman -S cpupower
fi


