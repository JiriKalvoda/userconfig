#!/bin/bash

cd ~/.tunel

. config


whileok()
{
	while true
	do
		sleep $checktime
		./ssh-check $server -p $port "echo OK > $okfile" -oStrictHostKeyChecking=no -oServerAliveInterval=300&
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
	echo START
	./ssh-tunel $tunel $user@$server -fN -oStrictHostKeyChecking=no -oServerAliveInterval=300 &
	whileok
done

