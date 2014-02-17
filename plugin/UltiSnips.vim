" File: UltiSnips.vim
" Author: Holger Rapp <SirVer@gmx.de>
" Description: The Ultimate Snippets solution for Vim
"
" Testing Info:
"   See directions at the top of the test.py script located one
"   directory above this file.

if exists('did_UltiSnips_plugin') || &cp || version < 700
    finish
endif

" The Commands we define.
command! -nargs=? -complete=customlist,UltiSnips#FileTypeComplete UltiSnipsEdit
    \ :call UltiSnips#Edit(<q-args>)

command! -nargs=1 UltiSnipsAddFiletypes :call UltiSnips#AddFiletypes(<q-args>)

" Backwards compatible functions. Prefer the ones in autoload/.
function! UltiSnips_ExpandSnippet()
    return UltiSnips#ExpandSnippet()
endfunction

function! UltiSnips_ExpandSnippetOrJump()
    return UltiSnips#ExpandSnippetOrJump()
endfunction

function! UltiSnips_SnippetsInCurrentScope()
    return UltiSnips#SnippetsInCurrentScope()
endfunction

function! UltiSnips_JumpBackwards()
    return UltiSnips#JumpBackwards()
endfunction

function! UltiSnips_JumpForwards()
    return UltiSnips#JumpForwards()
endfunction

function! UltiSnips_AddSnippet(...)
    return call(function('UltiSnips#AddSnippet'), a:000)
endfunction

function! UltiSnips_Anon(...)
    return call(function('UltiSnips#Anon'), a:000)
endfunction

au CursorMovedI * call UltiSnips#CursorMoved()
au CursorMoved * call UltiSnips#CursorMoved()
au BufLeave * call UltiSnips#LeavingBuffer()
au InsertLeave * call UltiSnips#LeavingInsertMode()

call UltiSnips#map_keys#MapKeys()

let did_UltiSnips_plugin=1

" vim: ts=8 sts=4 sw=4
