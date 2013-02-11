"=============================================================================
" FILE: ultisnips_complete.vim
" AUTHOR:  Stanislav Golovanov<stgolovanov@gmail.com>
" Last Modified: 08 Feb 2013.
" License: MIT license  {{{
"     Permission is hereby granted, free of charge, to any person obtaining
"     a copy of this software and associated documentation files (the
"     "Software"), to deal in the Software without restriction, including
"     without limitation the rights to use, copy, modify, merge, publish,
"     distribute, sublicense, and/or sell copies of the Software, and to
"     permit persons to whom the Software is furnished to do so, subject to
"     the following conditions:
"
"     The above copyright notice and this permission notice shall be included
"     in all copies or substantial portions of the Software.
"
"     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
"     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
"     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"     IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
"     CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
"     TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
"     SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
" }}}
"=============================================================================

let s:save_cpo = &cpo
set cpo&vim

let s:source = {
      \ 'name' : 'ultisnips_complete',
      \ 'kind' : 'complfunc',
      \}

function! s:source.initialize() "{{{
  " Initialize.

  " Map completion function
  exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=g:UltiSnips_Complete()<cr>"
  exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips_ExpandSnippetOrJump()<cr>"

  call neocomplcache#set_dictionary_helper(
        \ g:neocomplcache_source_rank, 'ultisnips_complete', 8)
  call neocomplcache#set_completion_length('ultsnips_complete',
        \ g:neocomplcache_auto_completion_start_length)
endfunction"}}}

function! s:source.get_keyword_pos(cur_text) "{{{
  return match(a:cur_text, '\S\+$')
endfunction"}}}

function! s:source.get_complete_words(cur_keyword_pos, cur_keyword_str) "{{{
  let completions = s:get_words_list(a:cur_keyword_str, 1)
  return completions
endfunction"}}}

function! g:UltiSnips_Complete()
    call UltiSnips_ExpandSnippet()
    if g:ulti_expand_res == 0
        if pumvisible()
            return "\<C-n>"
        else
            call UltiSnips_JumpForwards()
            if g:ulti_jump_forwards_res == 0
                return "\<TAB>"
            endif
        endif
    endif
    return ""
endfunction

function! s:get_words_list(cur_word, possible)
python << EOF
import vim
import sys
sys.path.append(vim.eval("g:UltiSnipsPythonPath"))
from UltiSnips import UltiSnips_Manager
import UltiSnips._vim as _vim
cur_word = vim.eval("a:cur_word")
possible = True if vim.eval("a:possible") else False
rawsnips = UltiSnips_Manager._snips(cur_word, possible)

snips = []
for snip in rawsnips:
    display = {}
    display['real_name'] = snip.trigger
    display['menu'] = '<snip> ' + snip.description
    display['word'] = snip.trigger
    display['kind'] = '~'
    snips.append(display)

vim.command("return %s" % _vim.escape(snips))
EOF
endfunction

function! neocomplcache#sources#ultisnips_complete#define() "{{{
  return s:source
endfunction"}}}

let &cpo = s:save_cpo
unlet s:save_cpo

" vim: foldmethod=marker

