#!/bin/bash
cd "$(dirname "$0")"
cp config ~/.config/i3/config 
cp toggle-border ~/.config/i3/i3-toggle-border
sudo cp printscreengimp /usr/bin/
sudo chmod o+x /usr/bin/printscreengimp
if [ $1 == no ];
then
	exit;
fi
sudo pacman -S jq
sudo pacman -S xfce4-appfinder
