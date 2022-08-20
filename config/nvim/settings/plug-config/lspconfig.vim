" lua << EOF
" require'lspconfig'.clangd.setup{}
" require'lspconfig'.bashls.setup{}
" require'lspconfig'.vimls.setup{}
" require'lspconfig'.pylsp.setup{}
" require'lspconfig'.tsserver.setup{}
" EOF
" 
" " LSP config (the mappings used in the default file don't quite work right)
" nnoremap <silent> gd <cmd>lua vim.lsp.buf.definition()<CR>
" nnoremap <silent> gD <cmd>lua vim.lsp.buf.declaration()<CR>
" nnoremap <silent> gr <cmd>lua vim.lsp.buf.references()<CR>
" nnoremap <silent> gi <cmd>lua vim.lsp.buf.implementation()<CR>
" nnoremap <silent> K <cmd>lua vim.lsp.buf.hover()<CR>
" nnoremap <silent> <C-k> <cmd>lua vim.lsp.buf.signature_help()<CR>
" nnoremap <silent> <C-n> <cmd>lua vim.diagnostic.goto_prev()<CR>
" nnoremap <silent> <C-p> <cmd>lua vim.diagnostic.goto_next()<CR>
" nnoremap <silent> <M-CR> <cmd>lua vim.lsp.buf.code_action()<CR>
" nnoremap <silent> gsh :ClangdSwitchSourceHeader<CR>
" 
" auto-format
autocmd BufWritePre *.cc lua vim.lsp.buf.formatting_sync(nil, 100)
autocmd BufWritePre *.h lua vim.lsp.buf.formatting_sync(nil, 100)
autocmd BufWritePre *.py lua vim.lsp.buf.formatting_sync(nil, 100)

