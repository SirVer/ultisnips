let s:source = {
      \ 'name' : 'ultisnips',
      \ 'kind' : 'manual',
      \ 'mark' : '[U]',
      \ 'min_pattern_length' : 1,
      \ 'is_volatile' : 1,
      \ 'rank' : 10,
      \}

function! s:source.gather_candidates(context)
  return keys(UltiSnips#SnippetsInCurrentScope())
endfunction

function! neocomplete#sources#ultisnips#define()
  return s:source
endfunction
