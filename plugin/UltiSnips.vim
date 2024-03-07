if exists('did_plugin_ultisnips') || &cp
    finish
endif
let did_plugin_ultisnips=1

if version < 800
   echohl WarningMsg
   echom  "UltiSnips requires Vim >= 8.0"
   echohl None
   finish
endif

" Enable Post debug server config
if !exists("g:UltiSnipsDebugServerEnable")
   let g:UltiSnipsDebugServerEnable = 0
endif

if !exists("g:UltiSnipsDebugHost")
   let g:UltiSnipsDebugHost = 'localhost'
endif

if !exists("g:UltiSnipsDebugPort")
   let g:UltiSnipsDebugPort = 8080
endif

if !exists("g:UltiSnipsPMDebugBlocking")
   let g:UltiSnipsPMDebugBlocking = 0
endif


" The Commands we define.
command! -bang -nargs=? -complete=customlist,UltiSnips#FileTypeComplete UltiSnipsEdit
    \ :call UltiSnips#Edit(<q-bang>, <q-args>)

command! -nargs=1 UltiSnipsAddFiletypes :call UltiSnips#AddFiletypes(<q-args>)

augroup UltiSnips_AutoTrigger
    au!
    au InsertCharPre * call UltiSnips#TrackChange()
    au TextChangedI * call UltiSnips#TrackChange()
    if exists('##TextChangedP')
        au TextChangedP * call UltiSnips#TrackChange()
    endif
augroup END

call UltiSnips#map_keys#MapKeys()

" vim: ts=8 sts=4 sw=4
