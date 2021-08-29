""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
"""""""""""netrw""""""""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""

	" netrw settings
	let g:netrw_liststyle = 3
	let g:netrw_banner = 0
	let g:netrw_browse_split = 3	

	augroup netrw_mapping
	    autocmd!
	    autocmd filetype netrw call NetrwMapping()
	augroup END

	" netrw mappings are local to the buffer; add autocommand to automatically
	" call a function whenever entering a buffer whose filetype is netrw
	function! NetrwMapping()
		noremap <buffer> tl :tabnext<CR>
		noremap <buffer> th :tabprev<CR>
		noremap <buffer> tn :tabnew<CR>
	endfunction


