#!/bin/bash
cd "$(dirname "$0")"

cp config ~/.config/i3/config 
cp toggle-border ~/.config/i3/i3-toggle-border
cp kill ~/.config/i3/i3-kill
chmod o+x ~/.config/i3/i3-*

if [ "$1" == "mint" ];
then
	sudo apt install numlockx
	sudo apt install jq
	sudo cp printscreengimp /usr/bin/
	sudo chmod o+x /usr/bin/printscreengimp
fi
if [ "$1" == "arch" ];
then
	sudo pacman -S xdotool
	sudo pacman -S jq
	sudo cp printscreengimp /usr/bin/
	sudo chmod o+x /usr/bin/printscreengimp
fi
