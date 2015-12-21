let s:save_cpo = &cpo
set cpo&vim

let s:unite_source = {
      \ 'name': 'ultisnips',
      \ 'hooks': {},
      \ 'action_table': {},
      \ 'syntax' : 'uniteSource__Ultisnips',
      \ 'default_action': 'expand',
      \ }

let s:unite_source.action_table.preview = {
      \ 'description' : 'ultisnips snippets',
      \ 'is_quit' : 0,
      \ }

function! s:unite_source.hooks.on_syntax(args, context) abort
  syntax case ignore
  syntax match uniteSource__UltisnipsHeader /^.*$/
        \ containedin=uniteSource__Ultisnips
  syntax match uniteSource__UltisnipsTrigger /\v^\s.{-}\ze\s/ contained
        \ containedin=uniteSource__UltisnipsHeader
        \ nextgroup=uniteSource__UltisnipsDescription
  syntax match uniteSource__UltisnipsDescription /\v.{3}\s\zs\w.*$/ contained
        \ containedin=uniteSource__UltisnipsHeader

  highlight default link uniteSource__UltisnipsTrigger Identifier
  highlight default link uniteSource__UltisnipsDescription Statement
endfunction

function! s:unite_source.action_table.preview.func(candidate)
  " no nice preview at this point, cannot get snippet text
  let snippet_preview = a:candidate['word']
  echo snippet_preview
endfunction

let s:unite_source.action_table.expand = {
      \ 'description': 'expand the current snippet',
      \ 'is_quit': 1
      \}

function! s:unite_source.action_table.expand.func(candidate)
  let delCurrWord = (getline(".")[col(".")-1] == " ") ? "" : "diw"
  exe "normal " . delCurrWord . "a" . a:candidate['trigger'] . " "
  call UltiSnips#ExpandSnippet()
  return ''
endfunction

function! s:unite_source.get_longest_snippet_len(snippet_list)
  let longest = 0
  for snip in items(a:snippet_list)
    if strlen(snip['word']) > longest
      let longest = strlen(snip['word'])
    endif
  endfor
  return longest
endfunction

function! s:unite_source.gather_candidates(args, context)
  let default_val = {'word': '', 'unite__abbr': '', 'is_dummy': 0, 'source':
        \  'ultisnips', 'unite__is_marked': 0, 'kind': 'command', 'is_matched': 1,
        \    'is_multiline': 0}
  let snippet_list = UltiSnips#SnippetsInCurrentScope()
  let max_len = s:unite_source.get_longest_snippet_len(snippet_list)
  let canditates = []
  for snip in items(snippet_list)
    let curr_val = copy(default_val)
    let curr_val['word'] = printf('%-*s', max_len, snip[0]) . "     " . snip[1]
    let curr_val['trigger'] = snip[0]
    call add(canditates, curr_val)
  endfor
  return canditates
endfunction

function! unite#sources#ultisnips#define()
  return s:unite_source
endfunction

"unlet s:unite_source

let &cpo = s:save_cpo
unlet s:save_cpo
