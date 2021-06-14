#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"

if [ "$1" == "mint" ];
then
	sudo apt install numlockx
	sudo apt install jq
	sudo ln -sr printscreengimp /usr/bin/
	sudo chmod o+x /usr/bin/printscreengimp
fi
if [ "$1" == "arch" ];
then
	echo -e "exec i3" > ~/.xinitrc
	sudo pacman -S xdotool
	sudo pacman -S jq
	sudo ln -sr printscreengimp /usr/bin/
	sudo chmod o+x /usr/bin/printscreengimp
fi
