vim.api.nvim_set_keymap('n', '<leader>gb', ':BlamerToggle<CR>', {noremap = true})
vim.g.blamer_date_format = '%m/%d/%y'
vim.g.blamer_template = '<committer> | <commit-short> | <committer-time> | <summary>'
