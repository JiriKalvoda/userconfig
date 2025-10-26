
" Language server
lua <<AMEN
	require'lspconfig'.pylsp.setup{
		log_level = vim.lsp.protocol.MessageType.Log,
		-- message_level = vim.lsp.protocol.MessageType.Error,
		settings = {
			pylsp = {
				plugins = {
					pycodestyle = {
						enabled = false,
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

" Experiments with lspsaga by MJ
lua <<AMEN
	local saga = require 'lspsaga'
	saga.setup({
		symbol_in_winbar = {
			enable = false,
		}
	})

	local keymap = vim.keymap.set
	keymap("n", "gh", "<cmd>Lspsaga lsp_finder<CR>")
	keymap({"n","v"}, "<Bslash>ca", "<cmd>Lspsaga code_action<CR>")
	keymap("n", "gr", "<cmd>Lspsaga rename<CR>")
	keymap("n", "gr", "<cmd>Lspsaga rename ++project<CR>")
	keymap("n", "gp", "<cmd>Lspsaga peek_definition<CR>")
	keymap("n", "gd", "<cmd>Lspsaga goto_definition<CR>")
	keymap("n", "gp", "<cmd>Lspsaga peek_type_definition<CR>")
	keymap("n", "<Bslash>d", "<cmd>Lspsaga show_line_diagnostics<CR>")
	keymap("n", "<Bslash>D", "<cmd>Lspsaga show_buf_diagnostics<CR>")
	keymap("n", "[e", "<cmd>Lspsaga diagnostic_jump_prev<CR>")
	keymap("n", "]e", "<cmd>Lspsaga diagnostic_jump_next<CR>")
	keymap("n", "[E", function()
	  require("lspsaga.diagnostic"):goto_prev({ severity = vim.diagnostic.severity.ERROR })
	end)
	keymap("n", "]E", function()
	  require("lspsaga.diagnostic"):goto_next({ severity = vim.diagnostic.severity.ERROR })
	end)
	keymap("n", "K", "<cmd>Lspsaga hover_doc ++quiet<CR>")
	keymap("n", "<Leader>ci", "<cmd>Lspsaga incoming_calls<CR>")
	keymap("n", "<Leader>co", "<cmd>Lspsaga outgoing_calls<CR>")
AMEN

" Completion via nvim-cmp by MJ
lua <<EOF
  -- Setup nvim-cmp.
  local cmp = require'cmp'

  cmp.setup({
    completion = {
      -- autocomplete = false,
    },
    window = {
      completion = cmp.config.window.bordered(),
      documentation = cmp.config.window.bordered(),
    },
    mapping = cmp.mapping.preset.insert({
      -- ['<C-b>'] = cmp.mapping.scroll_docs(-4),
      -- ['<C-f>'] = cmp.mapping.scroll_docs(4),
      -- ['<C-Space>'] = cmp.mapping.complete(),
      ['<C-e>'] = cmp.mapping.abort(),
      ['<A-Tab>'] = cmp.mapping.confirm({ select = true }), -- Accept currently selected item. Set `select` to `false` to only confirm explicitly selected items.
      ["<C-n>"] = cmp.config.disable,
      ["<C-p>"] = cmp.config.disable,
    }),
    sources = cmp.config.sources({
      { name = 'nvim_lsp' },
    }, {
      { name = 'buffer' },
    })
  })
  -- Setup lspconfig.
  local capabilities = require('cmp_nvim_lsp').default_capabilities(vim.lsp.protocol.make_client_capabilities())
  require('lspconfig')['pylsp'].setup {
    capabilities = capabilities
  }
EOF
" inoremap <silent> <A-Tab> <Cmd>lua require('cmp').complete()<CR>

" autocmd FileType python nmap <silent> <Leader><Leader>D     <cmd>lua vim.lsp.buf.declaration()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>d     <cmd>lua vim.lsp.buf.definition()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>K     <cmd>lua vim.lsp.buf.hover()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>i     <cmd>lua vim.lsp.buf.implementation()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>h     <cmd>lua vim.lsp.buf.signature_help()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>t     <cmd>lua vim.lsp.buf.type_definition()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>R     <cmd>lua vim.lsp.buf.references()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>r     <cmd>lua vim.lsp.buf.rename()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>s     <cmd>lua vim.lsp.buf.document_symbol()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>W     <cmd>lua vim.lsp.buf.workspace_symbol()<CR>
" autocmd FileType python nmap <silent> <Leader><Leader>f     <cmd>lua vim.diagnostic.open_float()<CR>

" Enable snippet completion, using the ultisnips plugin
" let g:OmniSharp_want_snippet=1
