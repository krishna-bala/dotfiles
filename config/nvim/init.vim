" set runtimepath^=~/.vim runtimepath+=~/.vim/after
" let &packpath = &runtimepath
" source ~/.vimrc

" Installs vimplug if not already installed.
source ~/.config/nvim/plug-config/vim-plug_install.vim
source ~/.config/nvim/settings/plugins.vim
source ~/.config/nvim/settings/basic_settings.vim
source ~/.config/nvim/settings/colors.vim
source ~/.config/nvim/settings/mappings.vim
