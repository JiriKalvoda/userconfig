#!/bin/bash
cd "$(dirname "$0")"

cp vimrc ~/.vimrc
cp vimRun.sh ~/bin/vimRun
mkdir -p ~/.vimRun
mkdir -p ~/.basicFile
cp basicFile* ~/.basicFile

