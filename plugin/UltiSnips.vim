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
command! -bang -nargs=? -complete=customlist,UltiSnips#FileTypeComplete UltiSnipsEdit
    \ :call UltiSnips#Edit(<q-bang>, <q-args>)

command! -nargs=1 UltiSnipsAddFiletypes :call UltiSnips#AddFiletypes(<q-args>)

" Backwards compatible functions. Prefer the ones in autoload/.
function! UltiSnips_FileTypeChanged()
    echoerr "Deprecated UltiSnips_FileTypeChanged called. Please use UltiSnips#FileTypeChanged." | sleep 1
    return UltiSnips#FileTypeChanged()
endfunction

function! UltiSnips_ExpandSnippet()
    echoerr "Deprecated UltiSnips_ExpandSnippet called. Please use UltiSnips#ExpandSnippet." | sleep 1
    return UltiSnips#ExpandSnippet()
endfunction

function! UltiSnips_ExpandSnippetOrJump()
    echoerr "Deprecated UltiSnips_ExpandSnippetOrJump called. Please use UltiSnips#ExpandSnippetOrJump." | sleep 1
    return UltiSnips#ExpandSnippetOrJump()
endfunction

function! UltiSnips_SnippetsInCurrentScope()
    echoerr "Deprecated UltiSnips_SnippetsInCurrentScope called. Please use UltiSnips#SnippetsInCurrentScope." | sleep 1
    return UltiSnips#SnippetsInCurrentScope()
endfunction

function! UltiSnips_JumpBackwards()
    echoerr "Deprecated UltiSnips_JumpBackwards called. Please use UltiSnips#JumpBackwards." | sleep 1
    return UltiSnips#JumpBackwards()
endfunction

function! UltiSnips_JumpForwards()
    echoerr "Deprecated UltiSnips_JumpForwards called. Please use UltiSnips#JumpForwards." | sleep 1
    return UltiSnips#JumpForwards()
endfunction

function! UltiSnips_AddSnippet(...)
    echoerr "Deprecated UltiSnips_AddSnippet called. Please use UltiSnips#AddSnippetWithPriority." | sleep 1
    return call(function('UltiSnips#AddSnippet'), a:000)
endfunction

function! UltiSnips_Anon(...)
    echoerr "Deprecated UltiSnips_Anon called. Please use UltiSnips#Anon." | sleep 1
    return call(function('UltiSnips#Anon'), a:000)
endfunction

augroup UltiSnips
    au!
    au CursorMovedI * call UltiSnips#CursorMoved()
    au CursorMoved * call UltiSnips#CursorMoved()
    au BufLeave * call UltiSnips#LeavingBuffer()
    au InsertLeave * call UltiSnips#LeavingInsertMode()
augroup END

call UltiSnips#map_keys#MapKeys()

let did_UltiSnips_plugin=1

" vim: ts=8 sts=4 sw=4
