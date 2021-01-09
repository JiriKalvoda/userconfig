#!/bin/bash
cd "$(dirname "$0")"

sudo ln -sr tunel.sh /usr/bin/tunel
sudo chmod +x /usr/bin/tunel

sudo cp tunel.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable tunel

mkdir ~/.tunel -p
ln -s `which ssh` ~/.tunel/ssh-tunel
ln -s `which sleep` ~/.tunel/ssh-sleep
ln -s `which ssh` ~/.tunel/ssh-check
if [[ ! -f ~/.tunel/config ]]
then
	cp config ~/.tunel
fi


