#!/bin/bash
cd "$(dirname "$0")"

sudo cp tunel.sh /usr/bin/tunel
sudo chmod +x /usr/bin/tunel

sudo cp tunel.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable tunel

mkdir ~/.tunel -p
ln -s /usr/bin/ssh ~/.tunel/ssh-tunel
ln -s /usr/bin/ssh ~/.tunel/ssh-check
cp config ~/.tunel

