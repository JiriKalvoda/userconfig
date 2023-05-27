#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln movingssh ~/bin/
confln cssh ~/bin/
confln movingssh_complete ~/bin/bashrc/

confln rpi0 ~/bin/
confln rpi2 ~/bin/
confln rpi4 ~/bin/
confln poppi ~/bin/
confln gimli ~/bin/
confln nikam ~/bin/
confln kamtop ~/bin/
confln contest ~/bin/

mkdir -p ~/.movingssh/address
mkdir -p ~/.movingssh/tunel
mkdir -p ~/.movingssh/groups
mkdir -p ~/.movingssh/groups-complete
mkdir -p ~/m

confln config ~/.movingssh/ c

for i in groups/*
do
	confln $i ~/.movingssh/groups/ cr
done
for i in groups-complete/*
do
	confln $i ~/.movingssh/groups-complete/ cr
done

for i in configDevice/*
do
	confln $i ~/.movingssh/configDevice/ cr
done

install_ok
