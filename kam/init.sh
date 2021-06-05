#!/bin/bash
cd "$(dirname "$0")"

g++ kam.cpp -o ~/bin/kam -O2
mkdir ~/kam
confln  kam_complete.sh ~/bin/bashrc/
confln pub ~/bin/
