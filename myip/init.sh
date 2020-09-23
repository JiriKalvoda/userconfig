#!/bin/bash
cd "$(dirname "$0")"

sudo cp publicmyip.sh /usr/bin/publicmyip
sudo chmod +x /usr/bin/publicmyip
sudo cp myip.sh /usr/bin/myip
sudo chmod +x /usr/bin/myip

sudo cp publicmyip.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable publicmyip

mkdir ~/.publicmyip -p
if [[ ! -f ~/.publicmyip/config ]]
then
	cp config ~/.publicmyip
fi

if [[ ! -f ~/.publicmyip/configIp ]]
then
	cp configIp ~/.publicmyip
fi

if [[ ! -f ~/.publicmyip/myposition.sh ]]
then
	cp myposition.sh ~/.publicmyip
fi
chmod +x ~/.publicmyip/myposition.sh

sudo ln -s ~/.publicmyip/myposition.sh /usr/bin/myposition
