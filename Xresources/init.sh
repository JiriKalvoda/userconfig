#!/bin/bash
cd "$(dirname "$0")"

mkdir ~/.urxvt/
mkdir ~/.urxvt/ext/
cp new-window ~/.urxvt/ext/new-window
cp close-gracefully ~/.urxvt/ext/close-gracefully
cp Xresources ~/.Xresources
xrdb  ~/.Xresources
if [ $1 == "arch" ];
then
	aurman -S urxvt-resize-font-git
	#aurman -S urxvt-clipboard
	aurman -S urxvt-perls
	#cd ~/tmp
	#git clone https://aur.archlinux.org/urxvt-resize-font-git.git
	#cd urxvt-resize-font-git
	#makepkg -si
	#cd ..
	#yes | rm urxvt-resize-font-git -r
fi
