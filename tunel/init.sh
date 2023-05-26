#!/bin/bash
cd "$(dirname "$0")"

confln second-tunel.sh ~/bin/second-tunel
confln second-tunel-kill.sh ~/bin/second-tunel-kill

confln tunel.sh ~/bin/tunel


mkdir ~/.tunel -p
confln "`which ssh`" ~/.tunel/tunel-ssh
confln "`which ssh`" ~/.tunel/second-tunel-ssh
confln "`which ssh`" ~/.tunel/tunel-ssh-check

gcc tunel-echo.c -o ~/.tunel/tunel-echo
gcc tunel-echo.c -o ~/.tunel/second-tunel-echo

confln config ~/.tunel/ c
confln config-default ~/.tunel/

ssh -o HostKeyAlias=localhost localhost echo OK ssh localhost
. ~/.tunel/config-default
. ~/.tunel/config
ssh $user@$server echo OK ssh server
