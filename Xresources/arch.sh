#!/bin/bash
cd "$(dirname "$0")"
mkdir ~/.urxvt/ext/
cp new-window ~/.urxvt/ext/new-window
cp close-gracefully ~/.urxvt/ext/close-gracefully
cp Xresources ~/.Xresources
xrdb  ~/.Xresources
if [ $1 == no ];
then
	exit;
fi
cd ~/tmp
git clone https://aur.archlinux.org/urxvt-resize-font-git.git
cd urxvt-resize-font-git
makepkg -si
cd ..
yes | rm urxvt-resize-font-git -r
