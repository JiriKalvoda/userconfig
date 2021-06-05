#!/bin/bash
cd "$(dirname "$0")"

echo -e "\e[31mROOT REQUIRE\e[0m"
confln  offlineimap-jiri.service /lib/systemd/system/ cr
systemctl daemon-reload
systemctl enable offlineimap-jiri
systemctl start offlineimap-jiri

