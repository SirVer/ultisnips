if exists('did_plugin_ultisnips') || &cp
    finish
endif
let did_plugin_ultisnips=1

if version < 704
   echohl WarningMsg
   echom  "UltiSnips requires Vim >= 7.4"
   echohl None
   finish
endif

if !exists("g:UltiSnipsUsePythonVersion")
   let g:_uspy=":py3 "
   if !has("python3")
       if !has("python")
           if !exists("g:UltiSnipsNoPythonWarning")
               echohl WarningMsg
               echom  "UltiSnips requires py >= 2.7 or py3"
               echohl None
           endif
           unlet g:_uspy
           finish
       endif
       let g:_uspy=":py "
   endif
else
   " Use user-provided value, but check if it's available.
   " This uses `has()`, because e.g. `exists(":python3")` is always 2.
   if g:UltiSnipsUsePythonVersion == 2 && has('python')
       let g:_uspy=":python "
   elseif g:UltiSnipsUsePythonVersion == 3 && has('python3')
       let g:_uspy=":python3 "
   endif
   if !exists('g:_uspy')
       echohl WarningMsg
       echom  "UltiSnips: the Python version from g:UltiSnipsUsePythonVersion (".g:UltiSnipsUsePythonVersion.") is not available."
       echohl None
       finish
   endif
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

    au InsertLeave * call UltiSnips#LeavingInsertMode()

    au BufLeave * call UltiSnips#LeavingBuffer()
    au CmdwinEnter * call UltiSnips#LeavingBuffer()
    au CmdwinLeave * call UltiSnips#LeavingBuffer()
augroup END

call UltiSnips#map_keys#MapKeys()

" vim: ts=8 sts=4 sw=4
