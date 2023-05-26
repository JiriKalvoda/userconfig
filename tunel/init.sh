#!/bin/bash
cd "$(dirname "$0")"

confln second-tunel.sh ~/bin/second-tunel

confln tunel.sh ~/bin/tunel

mkdir ~/.tunel -p

gcc tunel-echo.c -o ~/.tunel/tunel-echo
gcc tunel-echo.c -o ~/.tunel/second-tunel-echo

confln config ~/.tunel/ c
confln config-default ~/.tunel/

ssh -o HostKeyAlias=localhost localhost echo OK ssh localhost
. ~/.tunel/config-default
. ~/.tunel/config
ssh $user@$server echo OK ssh server
