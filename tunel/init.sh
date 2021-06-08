#!/bin/bash
cd "$(dirname "$0")"

confln tunel.sh ~/bin/tunel
chmod +x ~/bin/tunel

mkdir ~/.tunel -p
confln "`which ssh`" ~/.tunel/ssh-tunel
confln "`which sleep`" ~/.tunel/ssh-sleep
confln "`which ssh`" ~/.tunel/ssh-check

confln config ~/.tunel/ c

