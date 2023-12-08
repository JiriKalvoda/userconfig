#!/bin/bash
cd "$(dirname "$0")"
. ../userconfig-lib.sh
install_begin

confln plugins_conf.vim ~/.config/nvim/

d=~/.config/nvim/pack/plugins/start
mkdir -p $d

r git_clupdate https://github.com/hrsh7th/cmp-buffer $d/cmp-buffer
r git_clupdate https://github.com/hrsh7th/cmp-cmdline $d/cmp-cmdline
r git_clupdate https://github.com/hrsh7th/cmp-nvim-lsp $d/cmp-nvim-lsp
r git_clupdate https://github.com/hrsh7th/cmp-path $d/cmp-path

r git_clupdate https://github.com/nvimdev/lspsaga.nvim.git $d/lspsaga.nvim
r git_clupdate https://github.com/hrsh7th/nvim-cmp $d/nvim-cmp

r git_clupdate https://github.com/neovim/nvim-lspconfig.git $d/nvim-lspconfig
r git_clupdate https://github.com/nvim-treesitter/nvim-treesitter.git  $d/nvim-treesitter
r git_clupdate https://github.com/nvim-treesitter/nvim-treesitter-textobjects   $d/nvim-treesitter-textobjects

r git_clupdate https://github.com/godlygeek/tabular.git $d/tabular
r git_clupdate https://github.com/mbbill/undotree $d/undotree

install_ok
