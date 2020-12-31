#!/bin/bash

cd ~/.tunel

. config

if [[ "$1" == "-p" ]]
then
	echo ip$2=\"$server\"
	echo port$2=\"$port\"
	exit 0
fi


whileok()
{
	while true
	do
		sleep $checktime
		./ssh-check $server -p $port "echo OK > $okfile" -oServerAliveInterval=300&
		sleep $timeout
		killall ssh-check -q
		if [[ -f $okfile ]]
		then
			rm $okfile 
		else
			echo RESET
			return;
		fi
	done
}

while true
do
	killall ssh-tunel -q
	killall ssh-sleep -q
	echo START
	sleep 10000000 | ./ssh-tunel $tunel $user@$server -oServerAliveInterval=300 "cat - tunel $name port $port from $(myip)"  &
	whileok
done

