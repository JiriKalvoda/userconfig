#!/bin/bash

whileok()
{
	for ((i=0;i<10;i++))
	do
		ping 8.8.8.8 -c 1 && i=0
		sleep 1
	done
}

while true
do
	whileok
	echo restart
	restart
done

