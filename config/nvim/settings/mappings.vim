""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
""""""""""MAPPINGS""""""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""

" Key Mappings
noremap <Down>		<NOP>
noremap <Up>			<NOP>
noremap <Left>		<NOP>
noremap <Right>		<NOP>

" Tabs
"cycle tabs
nnoremap <leader>tl			:tabnext<CR>
nnoremap <leader>th			:tabprev<CR>
"new tabs
nnoremap <leader>tn			:tabnew<CR>
nnoremap <leader>te			:tabedit<Space>
"open new tab and edit file name under cursor
nnoremap <leader>tgf    <C-w>gf
"close tabs
nnoremap <leader>td			:tabclose<CR>

" Buffers
nnoremap <leader>ls			:ls<CR>:buffer<Space>
nnoremap <leader>lsd		:ls<CR>:bd<Space>
"cycle
nnoremap <leader>bh			:bp<CR>
nnoremap <leader>bl			:bn<CR>
"close buffer
nnoremap <leader>bd			:bd<CR>
"expand current buff to full window
nnoremap <leader>ba			:ba<CR>

"""""""""""
" Windows "
"""""""""""

"window splits
nnoremap <leader>wv			<C-w>v
nnoremap <leader>ws			<C-w>s
"move curosr 1 win [h,j,k,l]
nnoremap <leader>wh			<C-w>h
nnoremap <leader>wj			<C-w>j
nnoremap <leader>wk			<C-w>k
nnoremap <leader>wl			<C-w>l
"delete window
nnoremap <leader>wd			:close<CR>
"make current window full screen (close others)
nnoremap <leader>wo			<C-w>o
nnoremap <leader>wx			<C-w>x
"move window to full [width,height] on [left,bottom,top,right]
nnoremap <leader>wH			<C-w>H
nnoremap <leader>wJ			<C-w>J
nnoremap <leader>wK			<C-w>K
nnoremap <leader>wL			<C-w>L
"open window new tab
nnoremap <leader>wT     <C-w>T
" Window resize
nnoremap <leader>wvr		:vertical resize 
nnoremap <leader>wr			:resize 
nnoremap <leader>w.			<C-w>>
nnoremap <leader>w,			<C-w><
nnoremap <leader>w=			<C-w>=
nnoremap <leader>w<     <C-w>-
nnoremap <leader>w>     <C-w>+

" Terminal
nnoremap <leader>t<Space>		:terminal<CR>
tnoremap <leader><Esc>			<C-\><C-n>
tnoremap <leader>ls					<C-\><C-n>:ls<CR>:buffer<Space>
tnoremap <leader>bh					<C-\><C-n>:bp<CR>
tnoremap <leader>bl					<C-\><C-n>:bn<CR>
tnoremap <leader>bd					<C-\><C-n>:bd!<CR>

" Esc
au VimEnter * silent! !xmodmap -e 'clear Lock' -e 'keycode 0x42 = Escape'
au VimLeave * silent! !xmodmap -e 'clear Lock' -e 'keycode 0x42 = Caps_Lock'

" Splits open at bottom and right
set splitright splitbelow 

" Shortcutting split navigation:
map <M-h> <C-w>h
map <M-k> <C-w>k
map <M-j> <C-w>j
map <M-l> <C-w>l

" stop c and s from yanking
nnoremap c "_c
xnoremap c "_c
nnoremap s "_s
xnoremap s "_s
nnoremap x "_x
xnoremap x "_x

" when indenting, keep items highlighted
vnoremap < <gv
vnoremap > >gv

" source $MYVIMRC
nnoremap <leader>sv :source $MYVIMRC<CR>

" nvim-treesitter apply folding for current window
nnoremap <leader>nf :set foldmethod=expr<CR>:set foldexpr=nvim_treesitter#foldexpr()<CR>
