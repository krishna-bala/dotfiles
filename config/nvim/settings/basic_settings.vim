""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
"""""""Basic Settings"""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""

set nocompatible
filetype plugin on
syntax on
let mapleader =";"
let maplocalleader = ";;"

set ignorecase	" Allow non-case-sensitive case when using only lowercase
set smartcase

set foldmethod=syntax 
set number relativenumber				" Turn on line numbers and relative number
set timeoutlen=400							" milliseconds waited for mapped sequence to complete.
set wildmode=longest,list,full	" Enable autocompletion:
set hlsearch										" Highlight Search

set nobackup		" disable swaps and backups
set noswapfile

set hidden			" open new file when the current buffer testing if this will
set ruler				" show line and column number of cursor
set cursorline	" Enable highlighting of current line
	
set expandtab							" use spaces instead of tabs
set autoindent							" autoindent based on line above
set smartindent							" smarter indent for C-like languages
set shiftwidth=2						" when using Shift + > or <
set softtabstop=2						" in insert mode
set tabstop=2								" set the space occupied by a regular tabset autoindent
set linebreak breakindent		" break line at 'break' character and indent to line indent
set mouse=a									" allow mouse wheel movement

hi clear SpellBad
hi SpellBad cterm=underline ctermfg=red
hi clear SpellCap
hi SpellCap cterm=underline ctermfg=green

" Disable automatic commenting on newline:
autocmd Filetype * setlocal formatoptions-=c formatoptions-=r formatoptions-=o

" set text width
au FileType text setlocal textwidth=78
set textwidth=78
" set formatoptions+=t
" set formatoptions-=l

