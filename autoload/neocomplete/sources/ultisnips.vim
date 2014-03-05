let s:save_cpo = &cpo
set cpo&vim

let s:source = {
      \ 'name' : 'ultisnips',
      \ 'kind' : 'keyword',
      \ 'rank' : 8,
      \ 'mark' : '[U]',
      \}

function! s:source.gather_candidates(context)
  return keys(UltiSnips#SnippetsInCurrentScope())
endfunction

function! neocomplete#sources#ultisnips#define()
  return s:source
endfunction

let &cpo = s:save_cpo
unlet s:save_cpo
