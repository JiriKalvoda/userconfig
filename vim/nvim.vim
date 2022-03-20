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

call plug#begin("~/.config/nvim/plugged")
Plug 'glacambre/firenvim', { 'do': { _ -> firenvim#install(0) } }
Plug 'neovim/nvim-lspconfig'
call plug#end()



" Language server
lua <<AMEN
	require'lspconfig'.pylsp.setup{
	log_file = "/tmp/lsplog",
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


highlight LspDiagnosticsDefaultError ctermfg=red
highlight LspDiagnosticsDefaultWarning ctermfg=yellow
highlight LspDiagnosticsDefaultInformation ctermfg=cyan
highlight LspDiagnosticsDefaultHint ctermfg=cyan
set signcolumn=yes:1
highlight SignColumn ctermbg=black
autocmd Filetype python setlocal omnifunc=v:lua.vim.lsp.omnifunc
nnoremap <silent> gd    <cmd>lua vim.lsp.buf.declaration()<CR>
nnoremap <silent> <c-]> <cmd>lua vim.lsp.buf.definition()<CR>
nnoremap <silent> K     <cmd>lua vim.lsp.buf.hover()<CR>
nnoremap <silent> gD    <cmd>lua vim.lsp.buf.implementation()<CR>
nnoremap <silent> <c-k> <cmd>lua vim.lsp.buf.signature_help()<CR>
nnoremap <silent> 1gD   <cmd>lua vim.lsp.buf.type_definition()<CR>
nnoremap <silent> gr    <cmd>lua vim.lsp.buf.references()<CR>
nnoremap <silent> gR    <cmd>lua vim.lsp.buf.rename()<CR>
nnoremap <silent> g0    <cmd>lua vim.lsp.buf.document_symbol()<CR>
nnoremap <silent> gW    <cmd>lua vim.lsp.buf.workspace_symbol()<CR>
nnoremap <silent> <Bslash>d <cmd>lua vim.lsp.diagnostic.show_line_diagnostics()<CR>

function! s:termclose() abort
	q
endfunction

autocmd TermClose *:$SHELL,*:\$SHELL call s:termclose()
tnoremap <silent> <C-[><C-[> <C-\><C-n>

autocmd TermOpen * setlocal nonumber norelativenumber
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
