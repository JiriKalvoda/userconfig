#!/bin/bash
cd "$(dirname "$0")"
cp bashrc ~/.bashrc
mkdir -p ~/bin/bashrc
echo "$1" >> ~/.bashrc
