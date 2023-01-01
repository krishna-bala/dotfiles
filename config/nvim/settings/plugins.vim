"""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""
""""""""""PLUGINS"""""""""""""
""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""

call plug#begin('~/.config/nvim/plugged')    

  """""""""""""""""""""
  " LSP & Semantic HL "
  """""""""""""""""""""
	Plug 'neovim/nvim-lspconfig'
 	Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}  
  Plug 'nvim-treesitter/nvim-treesitter-textobjects'
  " We recommend updating the parsers on update
  "Plug 'kabouzeid/nvim-lspinstall'
 
  """"""""""""""""""""
  " nvim-cmp section "
  """"""""""""""""""""
  Plug 'hrsh7th/cmp-nvim-lsp'
  Plug 'hrsh7th/cmp-buffer'
  Plug 'hrsh7th/cmp-path'
  Plug 'hrsh7th/cmp-cmdline' 
  Plug 'hrsh7th/nvim-cmp'
  Plug 'hrsh7th/cmp-vsnip'
  Plug 'hrsh7th/vim-vsnip'
  Plug 'windwp/nvim-autopairs'
  
  """"""""""""""""
  " Color Themes "
  """"""""""""""""
  " Plug 'joshdick/onedark.vim'
  Plug 'rmehri01/onenord.nvim'
  " Plug 'rebelot/kanagawa.nvim'
  " Plug 'monsonjeremy/onedark.nvim'
  Plug 'navarasu/onedark.nvim'
      " "Plug 'EdenEast/nightfox.nvim'
  "Plug 'mhartington/oceanic-next'
  "Plug 'haystackandroid/carbonized'
  "Plug 'romainl/Apprentice'
  "Plug 'navarasu/onedark.nvim'
  "Plug 'christianchiarulli/nvcode-color-schemes.vim'
  "Plug 'doums/darcula'
  "Plug 'briones-gabriel/darcula-solid.nvim'
  "Plug 'rktjmp/lush.nvim'
  "Plug 'projekt0n/github-nvim-theme'

  """""""""""""""""""""""""""""""""
  " Icons, Status Bars, Explorers "
  """""""""""""""""""""""""""""""""
      " "Plug 'vim-airline/vim-airline'
      " "Plug 'vim-airline/vim-airline-themes'
  Plug 'nvim-lualine/lualine.nvim'
  Plug 'akinsho/bufferline.nvim'
  Plug 'kyazdani42/nvim-tree.lua'
  Plug 'yamatsum/nvim-nonicons'
  Plug 'kyazdani42/nvim-web-devicons' " for file icons
  Plug 'SmiteshP/nvim-gps'
  "Plug 'simrat39/symbols-outline.nvim'

  """"""""""""""
  " Appearance "
  """"""""""""""
  "Plug 'folke/zen-mode.nvim'
  Plug 'smithbm2316/centerpad.nvim'
  " Plug 'Pocco81/TrueZen.nvim'
  "Plug 'junegunn/goyo.vim'
  "Plug 'junegunn/limelight.vim'
  "Plug 'folke/twilight.nvim'

  """""""""""""
  " Utilities "
  """""""""""""
  Plug 'mhinz/vim-signify'
  Plug 'liuchengxu/vim-which-key'
  Plug 'junegunn/fzf', { 'do': { -> fzf#install() } }
  Plug 'junegunn/fzf.vim'
  Plug 'BurntSushi/ripgrep'
  Plug 'airblade/vim-rooter'
  Plug 'karb94/neoscroll.nvim'
  Plug 'APZelos/blamer.nvim'
  Plug 'numToStr/Comment.nvim'
  Plug 'tpope/vim-fugitive'
  Plug 'tommcdo/vim-fubitive'
  Plug 'jdhao/better-escape.vim'
  " Plug 'wesleimp/stylua.nvim'
  " Plug 'mfussenegger/nvim-dap'
  "Plug 'sakhnik/nvim-gdb', { 'do': ':!./install.sh' }
 

  """""""""
  " Notes "
  """""""""
  "Plug 'nvim-neorg/neorg' | Plug 'nvim-lua/plenary.nvim'
  "Plug 'vimwiki/vimwiki'
  "Plug 'lervag/wiki.vim'
  "Plug 'lervag/wiki-ft.vim'

  """"""""""""""""
  " Experimental "
  """"""""""""""""
  Plug 'nvim-lua/plenary.nvim'
  " Plug 'nvim-telescope/telescope.nvim', { 'tag': '0.1.0' }
  " Plug 'nvim-telescope/telescope-fzf-native.nvim', { 'do': 'make' }

call plug#end()

" luafile   ~/.config/nvim/settings/plug-config/lua-server.lua
luafile   ~/.config/nvim/settings/plug-config/treesitter.lua
" luafile   ~/.config/nvim/settings/plug-config/cmp-config.lua
luafile   ~/.config/nvim/settings/plug-config/lspconfig.lua
" source    ~/.config/nvim/settings/plug-config/lspconfig.vim
source    ~/.config/nvim/settings/plug-config/vsnip.vim
luafile   ~/.config/nvim/settings/plug-config/autopairs.lua
source    ~/.config/nvim/settings/plug-config/nvim-tree.vim
source    ~/.config/nvim/settings/plug-config/airline.vim
luafile   ~/.config/nvim/settings/plug-config/lualine.lua
source    ~/.config/nvim/settings/plug-config/signify.vim
source    ~/.config/nvim/settings/plug-config/which-key.vim
source    ~/.config/nvim/settings/plug-config/fzf.vim
luafile   ~/.config/nvim/settings/plug-config/bufferline.lua
luafile   ~/.config/nvim/settings/plug-config/nvim-gps.lua
source    ~/.config/nvim/settings/plug-config/centerpad.vim
" source    ~/.config/nvim/settings/plug-config/TrueZen.lua
luafile   ~/.config/nvim/settings/plug-config/neoscroll.lua
luafile   ~/.config/nvim/settings/plug-config/blamer.lua
luafile   ~/.config/nvim/settings/plug-config/Comment.lua
source    ~/.config/nvim/settings/plug-config/better-escape.vim
" luafile   ~/.config/nvim/settings/plug-config/telescope.lua
" luafile   ~/.config/nvim/settings/plug-config/nvim-dap.lua
"luafile   ~/.config/nvim/settings/plug-config/zen-mode.lua
"source  ~/.config/nvim/settings/plug-config/nightfox.vim
"source  ~/.config/nvim/settings/plug-config/wiki.vim
"luafile ~/.config/nvim/settings/plug-config/nvim-lspinstall.lua
"source  ~/.config/nvim/settings/plug-config/lspconfig.vim
"luafile ~/.config/nvim/settings/plug-config/neorg.lua
"luafile ~/.config/nvim/settings/plug-config/twilight.lua
"source  ~/.config/nvim/settings/plug-config/nvim-gdb.vim
