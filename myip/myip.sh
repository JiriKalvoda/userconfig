#!/bin/bash

cd ~/.publicmyip

grepCMD="noprefixroute wlp"
awkCMD='{print $2}'
. configIp

ip addres | grep "$grepCMD"| awk "$awkCMD" | cut -d "/" -f 1 | head -n1
