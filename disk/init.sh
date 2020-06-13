#!/bin/bash
cd "$(dirname "$0")"
sudo g++ ./diskSleep.c -o /usr/bin/diskSleep
sudo chmod u+s /usr/bin/diskSleep
sudo cp ./diskSleepGUI.sh  /usr/bin/diskSleepGUI
sudo chmod o+x /usr/bin/diskSleepGUI
if [ "$1" == "arch" ];
then
	sudo pacman -S hdparm
	sudo pacman -S udisks2
fi


