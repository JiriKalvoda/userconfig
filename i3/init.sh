#!/bin/bash
cd "$(dirname "$0")"

mkdir -p ~/.config/i3
ln -sr config ~/.config/i3/config 
ln -sr toggle-border ~/.config/i3/i3-toggle-border
ln -sr kill ~/.config/i3/i3-kill
chmod o+x ~/.config/i3/i3-*

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
