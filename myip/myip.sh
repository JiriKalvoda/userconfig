#!/bin/bash

cd ~/.publicmyip

grepCMD="noprefixroute wlp"
awkCMD='{print $3}'
. configIp

ip -br addres | grep UP | grep "$grepCMD"| awk "$awkCMD" | cut -d "/" -f 1 | head -n1
