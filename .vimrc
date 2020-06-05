" Krishna's configurations

" Plugins
    call plug#begin('~/.config/nvim/plugged')    
    Plug 'arcticicestudio/nord-vim'
    Plug 'vimwiki/vimwiki'
	Plug 'lervag/vimtex'
	Plug 'dylanaraps/wal.vim'
	Plug '907th/vim-auto-save'
	call plug#end()

" colors
    colorscheme nord

" Basics
    set nocompatible
    filetype plugin on
    syntax on
    let mapleader =";"
	:let maplocalleader = ";;"
" Allow non-case-sensitive case when using only lowercase
    set ignorecase
    set smartcase

" Change SpellBad to red and underlined
    hi clear SpellBad
    hi SpellBad cterm=underline ctermfg=red
    hi clear SpellCap
    hi SpellCap cterm=underline ctermfg=green

" Turn on line numbers and relative number
    set number relativenumber

" Time in milliseconds that is waited for a mapped sequence to complete.
    set timeoutlen=250

" Enable autocompletion:
    set wildmode=longest,list,full

" Disable automatic commenting on newline:
    autocmd Filetype * setlocal formatoptions-=c formatoptions-=r formatoptions-=o

" Key Mappings
    noremap <Down>		<NOP>
    noremap <Up>		<NOP>
    noremap <Left>		<NOP>
    noremap <Right>		<NOP>
    nnoremap tl			:tabnext<CR>
	nnoremap th			:tabprev<CR>
	nnoremap tn			:tabnew<CR>
	au VimEnter * silent! !xmodmap -e 'clear Lock' -e 'keycode 0x42 = Escape'
    au VimLeave * silent! !xmodmap -e 'clear Lock' -e 'keycode 0x42 = Caps_Lock'

" Splits open at bottom and right
    set splitright splitbelow 

" Shortcutting split navigation:
    map <C-h> <C-w>h
    map <C-k> <C-w>k
    map <C-j> <C-w>j
    map <C-l> <C-w>l

" Highlight Search
    set hlsearch

" stop c and s from yanking
    nnoremap c "_c
    xnoremap c "_c
    nnoremap s "_s
    xnoremap s "_s

" set text width
    au FileType text setlocal textwidth=78

" disable swaps and backups
    set nobackup
    set noswapfile
    
" indentation with 2 or 4 spaces
    set noexpandtab       " use spaces instead of tabs
    set autoindent      " autoindent based on line above
    set smartindent     " smarter indent for C-like languages
    set shiftwidth=4    " when using Shift + > or <
    set softtabstop=4   " in insert mode
    set tabstop=4       " set the space occupied by a regular tabset autoindent
    set linebreak breakindent "break line at 'break' character and indent to line indent
" allow mouse wheel movement
    set mouse=a

" vimwiki: set syntax to markdown
    let g:vimwiki_list = [{'path': '~/vimwiki', 'syntax': 'markdown', 'ext': '.md'}] 

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

" vimtex settings
"	let g:vimtex_compiler_progname = 'nvr'
	let g:tex_flavor='latex'
	let g:vimtex_view_method='zathura'
	let g:vimtex_quickfix_mode=0
	set conceallevel=1
	let g:tex_conceal='abdmg'
"	let g:vimtex_compiler_latexmk = {
"        \ 'background' : 1,
"        \ 'build_dir' : '',
"        \ 'callback' : 1,
"        \ 'continuous' : 1,
"        \ 'executable' : 'latexmk',
"        \ 'hooks' : [],
"        \ 'options' : [
"        \   '-verbose',
"        \   '-file-line-error',
"        \   '-synctex=1',
"        \   '-interaction=nonstopmode',
"        \ ],
"        \}

" vim-auto-save for tex files only
let g:auto_save = 0
augroup ft_tex
  au!
  au FileType tex let b:auto_save = 1
augroup END
