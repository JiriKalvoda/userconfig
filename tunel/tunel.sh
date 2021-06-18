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
		./$cmdprefix-ssh-check $server -p $port -oServerAliveInterval=300 -o HostKeyAlias=localhost "echo OK > $okfile" &
		sleep $timeout
		killall $cmdprefix-ssh-check -q
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
	killall $cmdprefix-echo -q
	killall $cmdprefix-ssh -q
	killall $cmdprefix-check -q
	echo START
	./$cmdprefix-echo |  ./$cmdprefix-ssh $tunel $user@$server -oServerAliveInterval=300 "./bin/tunel-server -- $name port $port from \$SSH_CLIENT local $(myip) start at \$(date \"+%y-%m-%d %H:%M:%S\")"  &
	whileok
done

