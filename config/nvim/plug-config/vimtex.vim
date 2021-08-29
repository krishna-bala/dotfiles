""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
"""""""""""vimtex"""""""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""

	" vimtex settings
	
	hi clear Conceal
	let g:vimtex_compiler_progname = 'nvr'
	let g:tex_flavor='latex'
	let g:vimtex_view_method='zathura'
	let g:vimtex_quickfix_mode=0
	set conceallevel=1
	let g:tex_conceal='abdmgs'
	let g:vimtex_view_skim_reading_bar = 0
	let g:vimtex_compiler_latexmk = {
        \ 'background' : 1,
        \ 'build_dir' : '',
        \ 'callback' : 1,
        \ 'continuous' : 1,
        \ 'executable' : 'latexmk',
        \ 'hooks' : [],
        \ 'options' : [
        \   '-verbose',
        \   '-file-line-error',
        \   '-synctex=1',
        \   '-interaction=nonstopmode',
        \ ],
        \}

	" vim-auto-save for tex files only
	let g:auto_save = 0
	augroup ft_tex
	  au!
	  au FileType tex let b:auto_save = 1
	augroup END


