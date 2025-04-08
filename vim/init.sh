#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
version 1
install_begin

confln vimrc ~/.vimrc
confln nvim.vim ~/.config/nvim/init.vim
confln vimRun.sh ~/bin/vimRun
confln vim_launcher ~/bin/vim_launcher
confln bash-rc ~/bin/bash-rc
mkdir -p ~/.vimRun
mkdir -p ~/.basicFile
mkdir -p ~/.local/state/vim/undo/
for i in basicFile*
do
	confln $i ~/.basicFile/
done

install_ok
