#!/bin/bash
cd "$(dirname "$0")"
sudo g++ ./cpuF.c -o /usr/bin/cpuF
sudo chmod u+s /usr/bin/cpuF
sudo cp ./cpuFGUI.sh  /usr/bin/cpuFGUI
sudo chmod o+x /usr/bin/cpuFGUI
if [ "$1" == "arch" ];
then
	sudo pacman -S cpupower
fi


