#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"

g++ ./volumeInfo.c -o /usr/bin/volumeInfo
chmod u+s /usr/bin/volumeInfo
cp ./volumeGUI.sh  /usr/bin/volumeGUI
chmod o+x /usr/bin/volumeGUI


