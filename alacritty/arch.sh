#!/bin/bash
cd "$(dirname "$0")"
mkdir -p ~/.config/alacritty
cp alacritty.yml ~/.config/alacritty/alacritty.yml
if [ "$1" == no ];
then
	exit;
fi
