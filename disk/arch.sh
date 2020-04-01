#!/bin/bash
cd "$(dirname "$0")"
if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root" ; exit 1 ; fi
g++ ./diskSleep.c -o /usr/bin/diskSleep
chmod u+s /usr/bin/diskSleep
cp ./diskSleepGUI.sh  /usr/bin/diskSleepGUI
chmod o+x /usr/bin/diskSleepGUI
if [ "$1" == no ];
then
	exit;
fi
sudo pacman -S hdparm
sudo pacman -S udisks2


