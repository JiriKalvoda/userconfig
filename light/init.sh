#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"

g++ ./light.c -o /usr/bin/light
chmod u+s /usr/bin/light
g++ ./lightInfo.c -o /usr/bin/lightInfo
chmod u+s /usr/bin/lightInfo
cp ./lightGUI.sh  /usr/bin/lightGUI
chmod o+x /usr/bin/lightGUI
