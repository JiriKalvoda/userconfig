#!/bin/bash
cd "$(dirname "$0")"
mkdir -p ~/.config/alacritty
ln -sr alacritty.yml ~/.config/alacritty/alacritty.yml
ln -sr  spawn-alacritty-cwd ~/.config/alacritty/spawn-alacritty-cwd
