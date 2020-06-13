#!/bin/bash
cd "$(dirname "$0")"

sudo g++ ./volumeInfo.c -o /usr/bin/volumeInfo
sudo chmod u+s /usr/bin/volumeInfo
sudo cp ./volumeGUI.sh  /usr/bin/volumeGUI
sudo chmod o+x /usr/bin/volumeGUI


