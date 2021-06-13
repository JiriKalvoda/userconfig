#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"
#confln  tunel.service /lib/systemd/system/ cr
#systemctl daemon-reload
#systemctl enable tunel
#systemctl start tunel

../init-service.sh tunel "$1" tunel
../init-service.sh second-tunel "$1" second-tunel "" d
