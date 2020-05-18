#!/bin/bash
cd "$(dirname "$0")"
g++ kam.cpp -o ~/bin/kam -O2
mkdir ~/kam
if [[ "$1" == "complete" ]];
then
	echo init autocomplete
	cat  kam_complete.sh >> ~/.bashrc
fi
