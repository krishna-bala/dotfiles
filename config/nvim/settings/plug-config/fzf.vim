nnoremap <localleader>f     :Files<CR>
nnoremap <localleader>g     :GFiles<CR>
nnoremap <localleader>m     :Maps<CR>
nnoremap <leader>ls         :Buffers<CR>
nnoremap <leader>bd         :BD<CR>
nnoremap <localleader>w     :Windows<CR>
nnoremap <leader>rg         :Rg<CR>
nnoremap <localleader>rg    :Rg!<CR>
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

