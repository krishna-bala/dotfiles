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
nnoremap <leader>ls			    :ls<CR>:buffer<Space>
nnoremap <leader>bd		      :ls<CR>:bd<Space>
"cycle
nnoremap <leader>bh			:bp<CR>
nnoremap <leader>bl			:bn<CR>
"expand current buff to full window
nnoremap <leader>ba			:ba<CR>

"""""""""""
" Splits "
"""""""""""

"window splits
nnoremap <localleader>vnH			:topleft    vnew<CR>
nnoremap <localleader>vnL			:botright   vnew<CR>
nnoremap <localleader>vnl			:rightbelow vnew<CR>
nnoremap <localleader>vnh			:leftabove  vnew<CR>

nnoremap <localleader>nK		  :topleft    new<CR>
nnoremap <localleader>nJ			:botright   new<CR>
nnoremap <localleader>nj			:rightbelow new<CR>
nnoremap <localleader>nk			:leftabove  new<CR>

"buffer splits
nnoremap <leader>vnH			:topleft    vsplit<CR>
nnoremap <leader>vnL			:botright   vsplit<CR>
nnoremap <leader>vnl			:rightbelow vsplit<CR>
nnoremap <leader>vnh			:leftabove  vsplit<CR>

nnoremap <leader>nK		  :topleft    split<CR>
nnoremap <leader>nJ			:botright   split<CR>
nnoremap <leader>nj			:rightbelow split<CR>
nnoremap <leader>nk			:leftabove  split<CR>

"""""""""""
" Windows "
"""""""""""

"Window navigation
nnoremap <leader>wh			<C-w>h
nnoremap <leader>wj			<C-w>j
nnoremap <leader>wk			<C-w>k
nnoremap <leader>wl			<C-w>l

" Window navigation
map <M-h> <C-w>h
map <M-k> <C-w>k
map <M-j> <C-w>j
map <M-l> <C-w>l

"delete window
nnoremap <leader>wd			:close<CR>

"make current window full screen (close others)
nnoremap <leader>wo			<C-w>o

"make current window full screen (close others)
nnoremap <leader>wT			<C-w>T

"rotate current focused window with closests window to the right
nnoremap <leader>wx			<C-w>x
nnoremap <leader>wR			<C-w>r

"move window to full [width,height] on [left,bottom,top,right]
nnoremap <leader>wH			<C-w>H
nnoremap <leader>wJ			<C-w>J
nnoremap <leader>wK			<C-w>K
nnoremap <leader>wL			<C-w>L

"open window new tab

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

" Esc
au VimEnter * silent! !xmodmap -e 'clear Lock' -e 'keycode 0x42 = Escape'
au VimLeave * silent! !xmodmap -e 'clear Lock' -e 'keycode 0x42 = Caps_Lock'

" Splits open at bottom and right
set splitright splitbelow 

" stop c, s, and x from yanking
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

" allows * to highlight and search but not jump (preserves jump list)
nnoremap * :keepjumps normal! mi*`i<CR>

" load quickfix item into previously used window
set switchbuf+=uselast

" turn off nvim lsp diagnostics (helpful when using git difftool)
nnoremap <leader>dh :lua vim.diagnostic.hide()<CR>

nnoremap <leader>so :let &scrolloff=999-&scrolloff<CR>

nnoremap <leader>y "+y
nnoremap <leader>v "+p
vnoremap <leader>y "+y
vnoremap <leader>v "+p
tnoremap <localleader>v <C-\><C-N>"+pi
