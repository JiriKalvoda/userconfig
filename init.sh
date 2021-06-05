#!/bin/bash

./confln confln ~/bin/

confirm="$1"
fromC=0
os="arch"
r()
{
	if [ "$1" -lt "$fromC" ]
	then
		return;
	fi
	sl="${@: -1:1}"
		echo -e -n "\e[1;95m$1 RUN: $sl\e[24;39;21m"
	if [ "$confirm" == "" ]
	then
		read -t 0.05 -n 10000 discard ; read -p   "[Y/n]?" input
		if [ "$input" != "n" ]
		then
			bash -c "$sl"
		fi
	elif [ "$confirm" == "y" ] 
	then
			bash -c "$sl"
	elif [ "$confirm" == "n" ] 
	then
		read -t 0.05 -n 10000 discard ; read -p   "[y/N]?" input
		if [ "$input" == "y" ]
		then
			bash -c "$sl"
		fi
	fi
}
r 1  "./alacritty/init.sh $os"
r 2  "./bash/init.sh $os"
r 3  "./cpu/init.sh $os"
r 4  "./disk/init.sh $os"
r 5  "./htop/init.sh $os"
r 6  "./keymap/init.sh $os"
r 7  "./i3/init.sh $os"
r 8  "./kam/init.sh $os"
r 9  "./keyboard/init.sh $os"
r 10 "./light/init.sh $os"
r 11  "./phone/init_desktop.sh $os"
r 12  "./rofi/init.sh $os"
r 13  "./vim/init.sh $os"
r 14  "./volume/init.sh $os"
r 15  "./Xresources/init.sh $os"
