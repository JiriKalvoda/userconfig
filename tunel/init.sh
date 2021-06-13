#!/bin/bash
cd "$(dirname "$0")"

confln second-tunel.sh ~/bin/second-tunel
confln second-tunel-kill.sh ~/bin/second-tunel-kill

confln tunel.sh ~/bin/tunel

gcc tunel-echo.c -o ~/.tunel/tunel-echo
gcc tunel-echo.c -o ~/.tunel/second-tunel-echo

mkdir ~/.tunel -p
confln "`which ssh`" ~/.tunel/tunel-ssh
confln "`which ssh`" ~/.tunel/second-tunel-ssh
confln "`which ssh`" ~/.tunel/tunel-ssh-check

confln config ~/.tunel/ c

ssh -o HostKeyAlias=localhost localhost echo OK ssh localhost
. ~/.tunel/config
ssh $user@$server echo OK ssh server
