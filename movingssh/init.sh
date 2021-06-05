#!/bin/bash
cd "$(dirname "$0")"

chmod +x movingssh
confln movingssh ~/bin/

confln rpi0 ~/bin/
confln rpi2 ~/bin/
confln rpi4 ~/bin/
confln poppi ~/bin/
confln gimli ~/bin/
confln nikam ~/bin/
confln kamtop ~/bin/

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
