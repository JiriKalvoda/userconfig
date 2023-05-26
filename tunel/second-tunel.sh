#!/bin/bash

cd ~/.tunel
cmdprefix=second-tunel

. config-default
. config

port=$(( port  + 1 ))
tunel="-R *:$port:localhost:22"

killall $cmdprefix-echo -q
killall $cmdprefix-ssh -q
echo START
(
	while true
	do
		sleep 10
		echo DOING ECHO >&2
		echo -n a
	done
) |  ssh $tunel $user@$server -oServerAliveInterval=300 "./bin/tunel-server  no -- $name port $port from \$SSH_CLIENT local $(myip) start at \$(date \"+%y-%m-%d %H:%M:%S\")" 

