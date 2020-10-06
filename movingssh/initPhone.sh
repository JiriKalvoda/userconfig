#!/bin/bash
cd "$(dirname "$0")"

chmod +x movingssh
cp movingssh ~/../usr/bin/
mkdir -p ~/.movingssh
mkdir -p ~/m
if [[ ! -f ~/.movingssh/config ]]
then
	cp config ~/.movingssh
fi
