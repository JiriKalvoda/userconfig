#!/bin/bash
cd "$(dirname "$0")"

bin=/data/data/com.termux/files/usr/bin

cp publicmyip.sh $bin/publicmyip
chmod +x $bin/publicmyip
cp myip.sh $bin/myip
chmod +x $bin/myip


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

ln -s ~/.publicmyip/myposition.sh $bin/myposition
