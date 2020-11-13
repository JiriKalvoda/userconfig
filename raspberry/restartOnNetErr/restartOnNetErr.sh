#!/bin/bash

whileok()
{
	for ((i=0;i<3;i++))
	do
		sleep 10
		ping 8.8.8.8 -c 1 >/dev/null && i=0
	done
}

while true
do
	whileok
	echo reboot
	reboot
done

