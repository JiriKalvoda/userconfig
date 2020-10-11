#!/bin/bash
cd "$(dirname "$0")"

sudo ln -sr offlineimap-run /usr/bin
sudo g++ offlineimap-deamon.cpp -o /usr/bin/offlineimap-deamon

sudo ln -sr offlineimap-jiri.service /lib/systemd/system
sudo ln -sr mailcap /etc/
sudo systemctl daemon-reload
sudo systemctl enable offlineimap-jiri

ln -sr .neomuttrc ~/.config/neomutt