#!/bin/bash
cd "$(dirname "$0")"

confln vimrc ~/.vimrc
confln nvim.vim ~/.config/nvim/init.vim
confln vimRun.sh ~/bin/vimRun
confln vim_launcher ~/bin/vim_launcher
confln bash-rc ~/bin/bash-rc
mkdir -p ~/.vimRun
mkdir -p ~/.basicFile
for i in basicFile*
do
	confln $i ~/.basicFile/
done

