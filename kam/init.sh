#!/bin/bash
cd "$(dirname "$0")"

g++ kam.cpp -o kam.out -O2
ln -sr kam.out ~/bin/kam
mkdir ~/kam
ln -sr  kam_complete.sh ~/bin/bashrc
