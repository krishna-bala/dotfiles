""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
"""""""""UltiSnips""""""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
	

	" UltiSnips settings
	let g:UltiSnipsExpandTrigger= "<tab>"

	" Use tab to switch to the next trigger point, shift+tab to previous trigger point
	let g:UltiSnipsJumpForwardTrigger = "<C-j>"
	let g:UltiSnipsJumpBackwardTrigger = "<C-k>"

	" Open UltiSnipsEdit in vertical split
	let g:UltiSnipsEditSplit = "tabdo"

	" Set UltiSnips directories for new snippets and where to look for snippets 
	" TODO: RESOLVE HOW TO SET NEW SNIPPETS AND WHERE TO SCAN FOR ALREADY EST. SNIPPETS
	" set runtimepath+=~/.config/nvim/plugged/
	" set runtimepath+=~/.config/nvim/
	"let g:UltiSnipsSnippetStorageDir=[$HOME.'/.config/nvim/krish_snippets/UltiSnips/']
	let g:UltiSnipsSnippetDirectories=['krish_snippets', '/home/krish/.config/nvim/plugged/vim-snippets/UltiSnips/'] " , '/home/krish/.config/nvim/plugged/vim-snippets/snippets/']

	" UltiSnips KeyMapping
	noremap <leader>ue	:UltiSnipsEdit

