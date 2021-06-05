#!/bin/bash
cd "$(dirname "$0")"

confln publicmyip.sh ~/bin/publicmyip
chmod +x ~/bin/publicmyip
confln myip.sh /usr/bin/myip
chmod +x ~/bin/myip

mkdir ~/.publicmyip -p
confln config ~/.publicmyip/ c
confln configIp ~/.publicmyip/ c
confln myposition.sh ~/.publicmyip/ c

chmod +x ~/.publicmyip/myposition.sh

confln ~/.publicmyip/myposition.sh ~/bin/myposition
