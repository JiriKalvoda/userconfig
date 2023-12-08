so ~/.vimrc
set guicursor=
"vmap <LeftRelease> "*ygv
"vmap p "0p

function! ExecHere()
	AddBash
	execute "tabnew | terminal ".g:toExec."echo"
	tabm -1
	normal i
	let g:toExec = ""
endfunction


" Exceptions for Firenvim
if exists('g:started_by_firenvim')
	set laststatus=0
endif

if !empty(expand(glob("~/.config/nvim/plugins_conf.vim")))
	so ~/.config/nvim/plugins_conf.vim
endif

