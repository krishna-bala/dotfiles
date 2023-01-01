nnoremap <localleader>f     :Files<CR>
" nnoremap <localleader>f     :Telescope find_files<CR>
nnoremap <localleader>g     :GFiles<CR>
" nnoremap <localleader>g     :Telescope git_files<CR>
nnoremap <localleader>m     :Maps<CR>
" nnoremap <localleader>m     :Telescope keymaps<CR>
nnoremap <leader>ls         :Buffers<CR>
" nnoremap <leader>ls         :Telescope buffers<CR>
nnoremap <leader>bd         :BD<CR>
nnoremap <localleader>w     :Windows<CR>
nnoremap <leader>rg         :Rg<CR>
" nnoremap <leader>rg         :Telescope live_grep<CR>
nnoremap <localleader>rg    :Rg!<CR>
" nnoremap <localleader>rg    :lua require('telescope.builtin').live_grep({layout_strategy='horizontal',layout_config={width=0.99, height=0.99, preview_width=0.5}})<CR>
nnoremap <localleader>bl    :BLines<CR>
nnoremap <localleader>l     :Lines<CR>

let g:fzf_layout = { 'down': '50%' }

function! s:list_buffers()
  redir => list
  silent ls
  redir END
  return split(list, "\n")
endfunction

function! s:delete_buffers(lines)
  execute 'bwipeout' join(map(a:lines, {_, line -> split(line)[0]}))
endfunction

command! BD call fzf#run(fzf#wrap({
  \ 'source': s:list_buffers(),
  \ 'sink*': { lines -> s:delete_buffers(lines) },
  \ 'options': '--multi --reverse --bind ctrl-a:select-all+accept'
\ }))

