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
nnoremap <leader>tl			:tabnext<CR>
nnoremap <leader>th			:tabprev<CR>
nnoremap <leader>tn			:tabnew<CR>
nnoremap <leader>te			:tabedit<Space>
nnoremap <leader>td			:tabclose<CR>

" Buffers
nnoremap <leader>ls			:ls<CR>:buffer<Space>
nnoremap <leader>lsd		:ls<CR>:bd<Space>
nnoremap <leader>bp			:bp<CR>
nnoremap <leader>bn			:bn<CR>
nnoremap <leader>bd			:bd<CR>
nnoremap <leader>ba			:ba<CR>

" Windows
nnoremap <leader>wv			<C-w>v
nnoremap <leader>ws			<C-w>s
nnoremap <leader>wh			<C-w>h
nnoremap <leader>wj			<C-w>j
nnoremap <leader>wk			<C-w>k
nnoremap <leader>wl			<C-w>l
nnoremap <leader>wd			:close<CR>
nnoremap <leader>wo			<C-w>o

" Window resize
nnoremap <leader>wr			:vertical resize 
nnoremap <leader>w+			:vertical resize +
nnoremap <leader>w-			:vertical resize -
nnoremap <leader>w=			<C-w>=

" Terminal
nnoremap <leader>t<Space>		:terminal<CR>
tnoremap <leader><Esc>			<C-\><C-n>
tnoremap <leader>ls					<C-\><C-n>:ls<CR>:buffer<Space>
tnoremap <leader>bp					<C-\><C-n>:bp<CR>
tnoremap <leader>bn					<C-\><C-n>:bn<CR>
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
