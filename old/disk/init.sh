#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"


g++ ./diskSleep.c -o /usr/bin/diskSleep
chmod u+s /usr/bin/diskSleep
cp ./diskSleepGUI.sh  /usr/bin/diskSleepGUI
chmod o+x /usr/bin/diskSleepGUI

if [ "$1" == "arch" ];
then
	pacman -S hdparm
	pacman -S udisks2
fi


