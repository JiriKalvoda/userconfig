#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"
#confln publicmyip.service /lib/systemd/system/ cr
#systemctl daemon-reload
#systemctl enable publicmyip
#systemctl restart publicmyip

../init-service.sh publicmyip "$1" publicmyip

