" Set some sane defaults for snippet files

if exists('b:did_ftplugin')
    finish
endif
let b:did_ftplugin = 1

let s:save_cpo = &cpo
set cpo&vim

" Fold by syntax, but open all folds by default
setlocal foldmethod=syntax
setlocal foldlevel=99

setlocal commentstring=#%s

setlocal noexpandtab
setlocal autoindent nosmartindent nocindent

" Whenever a snippets file is written, we ask UltiSnips to reload all snippet
" files. This feels like auto-updating, but is of course just an
" approximation: If files change outside of the current Vim instance, we will
" not notice.
augroup ultisnips_snippets.vim
autocmd!
autocmd BufWritePost <buffer> call UltiSnips#RefreshSnippets()
augroup END

" Define match words for use with matchit plugin
" http://www.vim.org/scripts/script.php?script_id=39
if exists("loaded_matchit") && !exists("b:match_words")
  let b:match_ignorecase = 0
  function! s:set_match_words() abort
    let pairs = [
                \ ['^snippet\>', '^endsnippet\>'],
                \ ['^global\>', '^endglobal\>'],
                \ ]

    " Note: Keep the related patterns into a pattern
    " Because tabstop-patterns such as ${1}, ${1:foo}, ${VISUAL}, ..., end with
    " the same pattern, '}', matchit could fail to get corresponding '}' in
    " nested patterns like ${1:${VISUAL:bar}} when the end-pattern is simply
    " set to '}'.
    call add(pairs, ['\${\%(\d\|VISUAL\)|\ze.*\\\@<!|}', '\\\@<!|}']) " ${1|baz,qux|}
    call add(pairs, ['\${\%(\d\|VISUAL\)\/\ze.*\\\@<!\/[gima]*}', '\\\@<!\/[gima]*}']) " ${1/garply/waldo/g}
    call add(pairs, ['\${\%(\%(\d\|VISUAL\)\:\ze\|\ze\%(\d\|VISUAL\)\).*\\\@<!}', '\\\@<!}']) " ${1:foo}, ${VISUAL:bar}, ... or ${1}, ${VISUAL}, ...
    call add(pairs, ['\\\@<!`\%(![pv]\|#!\/\f\+\)\%( \|$\)', '\\\@<!`']) " `!p quux`, `!v corge`, `#!/usr/bin/bash grault`, ... (indicators includes a whitespace or end-of-line)

    let pats = map(deepcopy(pairs), 'join(v:val, ":")')
    let match_words = join(pats, ',')
    return match_words
  endfunction
  let b:match_words = s:set_match_words()
  delfunction s:set_match_words
  let s:set_match_words = 1
endif

" Add TagBar support
let g:tagbar_type_snippets = {
            \ 'ctagstype': 'UltiSnips',
            \ 'kinds': [
                \ 's:snippets',
            \ ],
            \ 'deffile': expand('<sfile>:p:h:h') . '/ctags/UltiSnips.cnf',
        \ }

" don't unset g:tagbar_type_snippets, it serves no purpose
let b:undo_ftplugin = "
            \ setlocal foldmethod< foldlevel< commentstring<
            \|setlocal expandtab< autoindent< smartindent< cindent<
            \|if get(s:, 'set_match_words')
                \|unlet! b:match_ignorecase b:match_words s:set_match_words
            \|endif
            \"

" snippet text object:
" iS: inside snippet
" aS: around snippet (including empty lines that follow)
fun! s:UltiSnippetTextObj(inner) abort
  normal! 0
  let start = search('^snippet', 'nbcW')
  let end   = search('^endsnippet', 'ncW')
  let prev  = search('^endsnippet', 'nbW')

  if !start || !end || prev > start
    return feedkeys("\<Esc>", 'n')
  endif

  exe end

  if a:inner
    let start += 1
    let end   -= 1

  else
    if search('^\S') <= (end + 1)
      exe end
    else
      let end = line('.') - 1
    endif
  endif

  exe start
  k<
  exe end
  normal! $m>gv
endfun

onoremap <silent><buffer> iS :<C-U>call <SID>UltiSnippetTextObj(1)<CR>
xnoremap <silent><buffer> iS :<C-U>call <SID>UltiSnippetTextObj(1)<CR>
onoremap <silent><buffer> aS :<C-U>call <SID>UltiSnippetTextObj(0)<CR>
xnoremap <silent><buffer> aS :<C-U>call <SID>UltiSnippetTextObj(0)<CR>

let &cpo = s:save_cpo
unlet s:save_cpo
