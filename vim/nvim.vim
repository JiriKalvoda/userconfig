so ~/.vimrc
set guicursor=
se ls=0
"vmap <LeftRelease> "*ygv
"vmap p "0p

function! ExecHere()
	AddBash
	execute "tabnew | terminal ".g:toExec."echo"
	normal i
	let g:toExec = ""
endfunction

packadd plug
call plug#begin("~/.config/nvim/plugged")
Plug 'glacambre/firenvim', { 'do': { _ -> firenvim#install(0) } }
Plug 'neovim/nvim-lspconfig'
call plug#end()

" Exceptions for Firenvim
if exists('g:started_by_firenvim')
	set laststatus=0
endif

" Language server
lua <<AMEN
	require'lspconfig'.pylsp.setup{
		log_level = vim.lsp.protocol.MessageType.Log,
		-- message_level = vim.lsp.protocol.MessageType.Error,
		settings = {
			pylsp = {
				plugins = {
					pycodestyle = {
						enabled = true,
						-- see ~/.config/pycodestyle
					},
					pylsp_mypy = {
						enabled = true,
					},
				},
			}
		},
	}
AMEN


" Language server
" lua <<AMEN
" 	require'lspconfig'.pylsp.setup{
" 	log_file = "/tmp/lsplog",
" 		log_level = vim.lsp.protocol.MessageType.Log,
" 		-- message_level = vim.lsp.protocol.MessageType.Error,
" 		settings = {
" 			pylsp = {
" 				plugins = {
" 					pycodestyle = {
" 						enabled = true,
" 						-- see ~/.config/pycodestyle
" 					},
" 					pylsp_mypy = {
" 						enabled = true,
" 					},
" 				},
" 			}
" 		},
" 	}
" AMEN


highlight LspDiagnosticsDefaultError ctermfg=red
highlight LspDiagnosticsDefaultWarning ctermfg=yellow
highlight LspDiagnosticsDefaultInformation ctermfg=cyan
highlight LspDiagnosticsDefaultHint ctermfg=cyan
set signcolumn=yes:1
highlight SignColumn ctermbg=black
autocmd Filetype python setlocal omnifunc=v:lua.vim.lsp.omnifunc


function! s:termclose() abort
	q
endfunction

autocmd TermClose *:$SHELL,*:\$SHELL call s:termclose()
tnoremap <silent> <C-[><C-[> <C-\><C-n>

autocmd TermOpen * setlocal nonumber norelativenumber nospell
"au TermOpen * au <buffer> BufEnter,WinEnter redraw!

"augroup terminal_settings
"autocmd!

"autocmd BufWinEnter,WinEnter te

"autocmd BufWinEnter,WinEnter term://* startinsert
"autocmd BufLeave term://* stopinsert

" Ignore various filetypes as those will close terminal automatically
" Ignore fzf, ranger, coc
"autocmd TermClose term://*
	  "\ if (expand('<afile>') !~ "fzf") && (expand('<afile>') !~ "ranger") && (expand('<afile>') !~ "coc") |
	  "\   call nvim_input('<CR>')  |
	  "\ endif
augroup END





" Use the vim-plug plugin manager: https://github.com/junegunn/vim-plug
" Remember to run :PlugInstall when loading this vimrc for the first time, so
" vim-plug downloads the plugins listed.
call plug#begin("~/.config/nvim/plugged")
Plug 'OmniSharp/omnisharp-vim'
Plug 'dense-analysis/ale'
call plug#end()

" Don't autoselect first omnicomplete option, show options even if there is only
" one (so the preview documentation is accessible). Remove 'preview', 'popup'
" and 'popuphidden' if you don't want to see any documentation whatsoever.
" Note that neovim does not support `popuphidden` or `popup` yet:
" https://github.com/neovim/neovim/issues/10996
if has('patch-8.1.1880')
  set completeopt=longest,menuone,popuphidden
  " Highlight the completion documentation popup background/foreground the same as
  " the completion menu itself, for better readability with highlighted
  " documentation.
  set completepopup=highlight:Pmenu,border:off
else
  set completeopt=longest,menuone,preview
  " Set desired preview window height for viewing documentation.
  set previewheight=5
endif

" Tell ALE to use OmniSharp for linting C# files, and no other linters.
let g:ale_linters = { 'cs': ['OmniSharp'] }

augroup omnisharp_commands
  autocmd!

  " Show type information automatically when the cursor stops moving.
  " Note that the type is echoed to the Vim command line, and will overwrite
  " any other messages in this space including e.g. ALE linting messages.
  autocmd CursorHold *.cs OmniSharpTypeLookup

  " The following commands are contextual, based on the cursor position.
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>d <Plug>(omnisharp_go_to_definition)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>u <Plug>(omnisharp_find_usages)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>i <Plug>(omnisharp_find_implementations)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>pd <Plug>(omnisharp_preview_definition)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>pi <Plug>(omnisharp_preview_implementations)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>t <Plug>(omnisharp_type_lookup)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>d <Plug>(omnisharp_documentation)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>s <Plug>(omnisharp_find_symbol)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>f <Plug>(omnisharp_fix_usings)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>h <Plug>(omnisharp_signature_help)
  autocmd FileType cs imap <silent> <buffer> <C-\> <Plug>(omnisharp_signature_help)

  " Navigate up and down by method/property/field
  autocmd FileType cs nmap <silent> <buffer> [[ <Plug>(omnisharp_navigate_up)
  autocmd FileType cs nmap <silent> <buffer> ]] <Plug>(omnisharp_navigate_down)
  " Find all code errors/warnings for the current solution and populate the quickfix window
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>cc <Plug>(omnisharp_global_code_check)
  " Contextual code actions (uses fzf, vim-clap, CtrlP or unite.vim selector when available)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>ca <Plug>(omnisharp_code_actions)
  " Repeat the last code action performed (does not use a selector)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>. <Plug>(omnisharp_code_action_repeat)
  autocmd FileType cs xmap <silent> <buffer> <Leader><Leader>. <Plug>(omnisharp_code_action_repeat)

  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>= <Plug>(omnisharp_code_format)

  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>r <Plug>(omnisharp_rename)

  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>R <Plug>(omnisharp_restart_server)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>S <Plug>(omnisharp_start_server)
  autocmd FileType cs nmap <silent> <buffer> <Leader><Leader>E <Plug>(omnisharp_stop_server)
augroup END

autocmd FileType python nmap <silent> <Leader><Leader>D     <cmd>lua vim.lsp.buf.declaration()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>d     <cmd>lua vim.lsp.buf.definition()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>K     <cmd>lua vim.lsp.buf.hover()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>i     <cmd>lua vim.lsp.buf.implementation()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>h     <cmd>lua vim.lsp.buf.signature_help()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>t     <cmd>lua vim.lsp.buf.type_definition()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>R     <cmd>lua vim.lsp.buf.references()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>r     <cmd>lua vim.lsp.buf.rename()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>s     <cmd>lua vim.lsp.buf.document_symbol()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>W     <cmd>lua vim.lsp.buf.workspace_symbol()<CR>
autocmd FileType python nmap <silent> <Leader><Leader>f     <cmd>lua vim.diagnostic.open_float()<CR>

" Enable snippet completion, using the ultisnips plugin
" let g:OmniSharp_want_snippet=1
