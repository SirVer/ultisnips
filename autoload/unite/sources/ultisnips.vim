let s:save_cpo = &cpo
set cpo&vim

let s:unite_source = {
      \ 'name': 'ultisnips',
      \ 'hooks': {},
      \ 'action_table': {},
      \ 'default_action': 'expand',
      \ }

let s:unite_source.action_table.preview = {
      \ 'description' : 'ultisnips snippets',
      \ 'is_quit' : 0,
      \ }

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

function! s:unite_source.gather_candidates(args, context)
  let default_val = {'word': '', 'unite__abbr': '', 'is_dummy': 0, 'source':
        \  'ultisnips', 'unite__is_marked': 0, 'kind': 'command', 'is_matched': 1,
        \    'is_multiline': 0}
  let snippet_list = UltiSnips#SnippetsInCurrentScope()
  let canditates = []
  for snip in items(snippet_list)
    let curr_val = copy(default_val)
    let curr_val['word'] = snip[0] . "     " . snip[1]
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
