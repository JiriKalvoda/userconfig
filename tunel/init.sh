#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh

install_begin

confln second-tunel.sh ~/bin/second-tunel
confln tunel.sh ~/bin/tunel

mkdir ~/.tunel -p

r gcc tunel-echo.c -o ~/.tunel/tunel-echo
r gcc tunel-echo.c -o ~/.tunel/second-tunel-echo

confln config ~/.tunel/ c
confln config-default ~/.tunel/

vim ~/.tunel/config

r ssh -o HostKeyAlias=localhost localhost echo OK ssh localhost
r -b '. ~/.tunel/config-default && . ~/.tunel/config && ssh $user@$server echo OK ssh server'

install_ok
