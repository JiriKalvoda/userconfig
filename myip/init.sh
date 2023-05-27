#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln publicmyip.sh ~/bin/publicmyip
confln myip.sh ~/bin/myip

r mkdir ~/.publicmyip -p
confln config ~/.publicmyip/ c
confln configIp ~/.publicmyip/ c
confln myposition.sh ~/.publicmyip/ c

confln ~/.publicmyip/myposition.sh ~/bin/myposition

install_ok
