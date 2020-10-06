#!/bin/bash
cd "$(dirname "$0")"

ln -sr vimrc ~/.vimrc
ln -sr vimRun.sh ~/bin/vimRun
mkdir -p ~/.vimRun
mkdir -p ~/.basicFile
ln -sr basicFile* ~/.basicFile

