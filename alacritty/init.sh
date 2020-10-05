#!/bin/bash
cd "$(dirname "$0")"
mkdir -p ~/.config/alacritty
ln -sr alacritty.yml ~/.config/alacritty/alacritty.yml
