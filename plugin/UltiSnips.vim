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

augroup UltiSnips_AutoTrigger
    au!
    au InsertCharPre * call UltiSnips#TrackChange()
    au TextChangedI * call UltiSnips#TrackChange()
augroup END

call UltiSnips#map_keys#MapKeys()

" Register ultisnips source for nvim-completion-manager
" https://github.com/roxma/nvim-completion-manager
"
" Registering a source via this autocmd will avoid error when NCM has not been
" installed yet. And it also avoid the loading of autoload/cm.vim on neovim
" startup, so that NCM won't affect neovim's startup time
au User CmSetup call cm#register_source({'name' : 'cm-ultisnips',
		\ 'priority': 7, 
		\ 'abbreviation': 'Snip',
		\ 'default_word_pattern': '\S+',
		\ 'cm_refresh_patterns':['(\S{3,})$'],
		\ 'cm_refresh': 'cm#sources#ultisnips#cm_refresh',
		\ })

" vim: ts=8 sts=4 sw=4
