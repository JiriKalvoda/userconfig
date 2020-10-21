#!/bin/bash
cd "$(dirname "$0")"

sudo chmod +x movingssh
sudo ln -sr movingssh /usr/bin/
ln -sr gitea ~/bin
mkdir -p ~/.movingssh
mkdir -p ~/m
if [[ ! -f ~/.movingssh/config ]]
then
	cp config ~/.movingssh
fi
