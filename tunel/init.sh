#!/bin/bash
cd "$(dirname "$0")"

confln tunel.sh ~/bin/tunel
chmod +x ~/bin/tunel

gcc tunel-echo.c -o ~/.tunel/tunel-echo

mkdir ~/.tunel -p
confln "`which ssh`" ~/.tunel/tunel-ssh
confln "`which ssh`" ~/.tunel/tunel-ssh-check

confln config ~/.tunel/ c

