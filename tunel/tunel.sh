#!/bin/bash

cd ~/.tunel
cmdprefix=tunel

. config-default
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
		ssh $server -p $port -oServerAliveInterval=300 -o HostKeyAlias=localhost "echo OK > $okfile" &
		pid_check=$!
		sleep $timeout
		kill $pid_check
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
	echo START
	(
		while true
		do
			sleep 10
			echo DOING ECHO >&2
			echo -n a
		done
	) |  ssh $tunel $user@$server -oServerAliveInterval=300 "./bin/tunel-server -- $name port $port from \$SSH_CLIENT local $(myip) start at \$(date \"+%y-%m-%d %H:%M:%S\")"  &
	pid_ssh=$!
	whileok
	kill $pid_ssh
done

