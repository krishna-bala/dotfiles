""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
""""""""""PLUGINS"""""""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""

call plug#begin('~/.config/nvim/plugged')    
	" Plug '907th/vim-auto-save'
	" Plug 'francoiscabrol/ranger.vim'
	Plug 'EdenEast/nightfox.nvim'
	" Plug 'neoclide/coc.nvim', {'branch': 'release'}
	" Plug 'jackguo380/vim-lsp-cxx-highlight'
	Plug 'vim-airline/vim-airline'
	Plug 'vim-airline/vim-airline-themes'
	Plug 'mhinz/vim-signify'
	Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}  " We recommend updating the parsers on update
	Plug 'neovim/nvim-lspconfig'
	Plug 'hrsh7th/nvim-cmp'
  Plug 'kyazdani42/nvim-web-devicons' " for file icons
  Plug 'kyazdani42/nvim-tree.lua'
  Plug 'liuchengxu/vim-which-key'
  Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
  Plug 'junegunn/fzf.vim'
  Plug 'BurntSushi/ripgrep'
  Plug 'airblade/vim-rooter'
	" Plug 'octol/vim-cpp-enhanced-highlight'
	" Plug 'doums/darcula'
	" Plug 'lervag/vimtex'
	" Plug 'SirVer/ultisnips'
	" Plug 'honza/vim-snippets'
	" Plug 'arcticicestudio/nord-vim'
	" Plug 'vimwiki/vimwiki'
	" Plug 'dylanaraps/wal.vim'
	" Plug 'rbgrouleff/bclose.vim' 
call plug#end()

"source ~/.config/nvim/plug-config/nightfox.vim
" source ~/.config/nvim/plug-config/coc.vim
" source ~/.config/nvim/plug-config/coc-explorer.vim
" source $HOME/.config/nvim/plug-config/coc-clangd.vim
source ~/.config/nvim/plug-config/airline.vim
luafile ~/.config/nvim/plug-config/treesitter.lua
source ~/.config/nvim/plug-config/lspconfig.vim
luafile ~/.config/nvim/plug-config/cmp-config.lua
source ~/.config/nvim/plug-config/nvim-tree.vim
source ~/.config/nvim/plug-config/which-key.vim
" source $HOME/.config/nvim/plug-config/netrw.vim
" source $HOME/.config/nvim/plug-config/ultisnips.vim
" source $HOME/.config/nvim/plug-config/vimtex.vim
" source $HOME/.config/nvim/plug-config/vimwiki.vim

