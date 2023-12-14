#!/bin/bash
cd "$(dirname "$0")"

if [ $1 == "arch" ];
then
	yay -S urxvt-resize-font-git
	yay -S urxvt-perls
	#aurman -S urxvt-clipboard
	#cd ~/tmp
	#git clone https://aur.archlinux.org/urxvt-resize-font-git.git
	#cd urxvt-resize-font-git
	#makepkg -si
	#cd ..
	#yes | rm urxvt-resize-font-git -r
fi

