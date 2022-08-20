let g:nvim_tree_width_in_percent = 20 "30 by default, can be width_in_columns or 'width_in_percent%'
let g:nvim_tree_auto_ignore_ft = [ 'startify', 'dashboard' ] "empty by default, don't auto open tree on specific filetypes.
nnoremap <leader>ntt :NvimTreeToggle<CR>
nnoremap <leader>ntr :NvimTreeRefresh<CR>
nnoremap <localleader>ntf :NvimTreeFindFile<CR>
" NvimTreeOpen, NvimTreeClose and NvimTreeFocus are also available if you need them

set termguicolors " this variable must be enabled for colors to be applied properly

" a list of groups can be found at `:help nvim_tree_highlight`
highlight NvimTreeFolderIcon guibg=blue
lua << EOF
-- following options are the default
require("nvim-tree").setup({
  -- disables netrw completely
  disable_netrw = true,
  -- hijack netrw window on startup
  hijack_netrw = true,
  -- open the tree when running this setup function
  open_on_setup = false,
  -- will not open on setup if the filetype is in this list
  ignore_ft_on_setup = {},
  -- opens the tree when changing/opening a new tab if the tree wasn't previously opened
  open_on_tab = false,
  -- hijacks new directory buffers when they are opened.
  hijack_directories   = {
    -- enable the feature
    enable = true,
    -- allow to open the tree if it was previously closed
    auto_open = true,
  },
  -- hijack the cursor in the tree to put it at the start of the filename
  hijack_cursor = false,
  -- updates the root directory of the tree on `DirChanged` (when your run `:cd` usually)
  sync_root_with_cwd = false,
  -- show lsp diagnostics in the signcolumn
  diagnostics = {
    enable = false,
    icons = {
      hint = "",
      info = "",
      warning = "",
      error = "",
    },
  },
  -- update the focused file on `BufEnter`, un-collapses the folders recursively until it finds the file
  update_focused_file = {
    -- enables the feature
    enable = false,
    -- update the root directory of the tree to the one of the folder containing the file if the file is not under the current root directory
    -- only relevant when `update_focused_file.enable` is true
    update_root = false,
    -- list of buffer names / filetypes that will not update the cwd if the file isn't found under the current root directory
    -- only relevant when `update_focused_file.update_cwd` is true and `update_focused_file.enable` is true
    ignore_list = {},
  },
  -- configuration options for the system open command (`s` in the tree by default)
  system_open = {
    -- the command to run this, leaving nil should work in most cases
    cmd  = "",
    -- the command arguments as a list
    args = {},
  },

  filters = {
    dotfiles = false,
    custom = {},
  },

  git = {
    enable = true,
    ignore = true,
    timeout = 500,
  },

  actions = {
    open_file = {
      window_picker = {
        enable = true, -- false by default, will disable the window picker.
        exclude = {
          filetype = {
            "packer",
            "qf",
          },
          buftype = {
            "terminal",
          },
        },
      },
      resize_window = true, -- if true the tree will resize itself after opening a file
      quit_on_open = true, -- closes tree when you open a file
    },
  },

  view = {
    -- width of the window, can be either a number (columns) or a string in `%`, for left or right side placement
    width = 30,
    -- height of the window, can be either a number (columns) or a string in `%`, for top or bottom side placement
    height = 30,
    -- side of the tree, can be one of 'left' | 'right' | 'top' | 'bottom'
    side = "left",
    mappings = {
      -- custom only false will merge the list with the default mappings
      -- if true, it will only use your list to set the mappings
      custom_only = false,
      -- list of mappings to set on the tree manually
      list = {},
    },
  },

  renderer = {
    add_trailing = true, -- append a trailing slash to folder names
    highlight_opened_files = "all", -- 0 -> "none", 1 -> "icon", 2 -> "name", 3 -> "all"
    root_folder_modifier = ":~",
    highlight_git = true, -- 0 by default, will enable file highlight for git attributes (can be used without the icons).
    group_empty = true, -- 0 by default, compact folders that only contain a single folder into one node in the file tree
    indent_markers = {
      enable = true -- shows indent markers when folders are open
    },
    special_files = {
      "README.md", 
      "Makefile", 
      "MAKEFILE", -- List of filenames that gets highlighted with NvimTreeSpecialFile
    },
    icons = {
      padding = " ", -- one space by default, used for rendering the space between the icon and the filename. Use with caution, it could break rendering if you set an empty string depending on your font.
      symlink_arrow = " >> ", -- defaults to " ➛ ". used as a separator between symlinks" source and target.
      show = {
        git = true,
        folder = true,
        file = true,
        folder_arrow = false,
      },
      glyphs = {
        default = "",
        symlink = "",
        git = {
          unstaged = "✗",
          staged = "✓",
          unmerged = "",
          renamed = "➜",
          untracked = "★",
          deleted = "",
          ignored = "◌",
        },
        folder = {
          arrow_open = "",
          arrow_closed = "",
          default = "",
          open = "",
          empty = "",
          empty_open = "",
          symlink = "",
          symlink_open = "",
        },
      },
    },
  },
  respect_buf_cwd = true, -- 0 by default, will change cwd of nvim-tree to that of new buffer's when opening nvim-tree.
})
EOF
