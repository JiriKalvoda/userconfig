#!/bin/bash
cd "$(dirname "$0")"

chmod +x movingssh
cp movingssh ~/../usr/bin/
ln -sr rpi0 ~/bin
ln -sr rpi4 ~/bin
ln -sr poppi ~/bin
ln -sr gimli ~/bin
ln -sr nikam ~/bin
mkdir -p ~/.movingssh
mkdir -p ~/m
if [[ ! -f ~/.movingssh/config ]]
then
	cp config ~/.movingssh
fi
