#!/bin/bash

cd ~/.tunel
cmdprefix=second-tunel

. config

port=$(( port  + 1 ))

killall $cmdprefix-echo -q
killall $cmdprefix-ssh -q
echo START
./$cmdprefix-echo |  ./$cmdprefix-ssh $tunel $user@$server -oServerAliveInterval=300 "./bin/tunel-server  no -- $name port $port from \$SSH_CLIENT local $(myip) start at \$(date \"+%y-%m-%d %H:%M:%S\")" 

