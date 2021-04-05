#!/bin/bash
cd "$(dirname "$0")"

sudo chmod +x movingssh
sudo ln -sr movingssh /usr/bin/
ln -sr rpi0 ~/bin
ln -sr rpi2 ~/bin
ln -sr rpi4 ~/bin
ln -sr poppi ~/bin
ln -sr gimli ~/bin
ln -sr nikam ~/bin
ln -sr kamtop ~/bin
mkdir -p ~/.movingssh
mkdir -p ~/.movingssh/groups
mkdir -p ~/.movingssh/groups-complete
mkdir -p ~/m
if [[ ! -f ~/.movingssh/config ]]
then
	cp config ~/.movingssh
fi

ln -sr groups/* ~/.movingssh/groups
ln -sr groups-complete/* ~/.movingssh/groups-complete
