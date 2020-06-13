#!/bin/bash
cd "$(dirname "$0")"

sudo g++ ./light.c -o /usr/bin/light
sudo chmod u+s /usr/bin/light
sudo g++ ./lightInfo.c -o /usr/bin/lightInfo
sudo chmod u+s /usr/bin/lightInfo
sudo cp ./lightGUI.sh  /usr/bin/lightGUI
sudo chmod o+x /usr/bin/lightGUI

if [ "$1" == "mint" ]
then 
	sudo apt install notify-osd
fi
