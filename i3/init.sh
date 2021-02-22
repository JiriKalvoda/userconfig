#!/bin/bash
cd "$(dirname "$0")"

mkdir -p ~/.config/i3
ln -sr master.tex ~/.config/i3/
ln -sr ~/.config/i3/i3.config ~/.config/i3/config
(cd ~/.config/i3/; tex keymap-i3)
ln -sr toggle-border ~/.config/i3/i3-toggle-border
ln -sr kill ~/.config/i3/i3-kill
ln -sr i3-restart ~/.config/i3/
ln -sr i3status.conf ~/.config/i3/
chmod o+x ~/.config/i3/i3-*
cat >~/.xinitrc <<EOF
exec i3
EOF
g++ status.cpp -o ~/.config/i3/status.out

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
