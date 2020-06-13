#!/bin/bash
cd "$(dirname "$0")"

g++ kam.cpp -o ~/bin/kam -O2
mkdir ~/kam
cp  kam_complete.sh ~/bin/bashrc
