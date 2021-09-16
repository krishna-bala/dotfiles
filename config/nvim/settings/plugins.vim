""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""
""""""""""PLUGINS"""""""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""

call plug#begin('~/.config/nvim/plugged')    

  """""""""""""""""""""
  " LSP & Semantic HL "
  """""""""""""""""""""
	Plug 'neovim/nvim-lspconfig'
	Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}  " We recommend updating the parsers on update

  """"""""""""""""""""
  " nvim-cmp section "
  """"""""""""""""""""
	Plug 'hrsh7th/nvim-cmp'
  Plug 'hrsh7th/cmp-buffer'
  Plug 'hrsh7th/cmp-nvim-lsp'
  Plug 'hrsh7th/vim-vsnip'
  Plug 'windwp/nvim-autopairs'
  
  """"""""""""""
  " Appearance "
  """"""""""""""
	"Plug 'EdenEast/nightfox.nvim'
  Plug 'mhartington/oceanic-next'
	Plug 'vim-airline/vim-airline'
	Plug 'vim-airline/vim-airline-themes'
  Plug 'kyazdani42/nvim-tree.lua'
  Plug 'kyazdani42/nvim-web-devicons' " for file icons

  """""""""""""
  " Utilities "
  """""""""""""
	Plug 'mhinz/vim-signify'
  Plug 'liuchengxu/vim-which-key'
  Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
  Plug 'junegunn/fzf.vim'
  Plug 'BurntSushi/ripgrep'
  Plug 'airblade/vim-rooter'

call plug#end()

"source ~/.config/nvim/plug-config/nightfox.vim
source ~/.config/nvim/plug-config/lspconfig.vim
luafile ~/.config/nvim/plug-config/treesitter.lua
luafile ~/.config/nvim/plug-config/cmp-config.lua
luafile ~/.config/nvim/plug-config/autopairs.lua
source ~/.config/nvim/plug-config/nvim-tree.vim
source ~/.config/nvim/plug-config/airline.vim
source ~/.config/nvim/plug-config/signify.vim
source ~/.config/nvim/plug-config/which-key.vim
source ~/.config/nvim/plug-config/fzf.vim

