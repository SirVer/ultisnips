let s:save_cpo = &cpo
set cpo&vim

let s:source = {
   \ 'name' : 'ultisnips',
   \ 'kind' : 'keyword',
   \ 'mark' : '[US]',
   \ 'rank' : 8,
   \ 'matchers' :
      \ (g:neocomplete#enable_fuzzy_completion ?
      \ ['matcher_fuzzy'] : ['matcher_head']),
   \ }

function! s:source.gather_candidates(context)
   let suggestions = []
   let snippets = UltiSnips#SnippetsInCurrentScope()
   for trigger in keys(snippets)
      let description = get(snippets, trigger)
      call add(suggestions, {
         \ 'word' : trigger,
         \ 'menu' : self.mark . ' '. description
         \ })
   endfor
   return suggestions
endfunction

function! neocomplete#sources#ultisnips#define()
   return s:source
endfunction

let &cpo = s:save_cpo
unlet s:save_cpo
