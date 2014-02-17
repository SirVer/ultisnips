call UltiSnips#variables#WasRun()

function! UltiSnips#map_keys#MapKeys()
    " Map the keys correctly
    if g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger

        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippetOrJump()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippetOrJump()<cr>"
    else
        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippet()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippet()<cr>"
    endif
    exec 'xnoremap ' . g:UltiSnipsExpandTrigger. ' :call UltiSnips#SaveLastVisualSelection()<cr>gvs'
    exec "inoremap <silent> " . g:UltiSnipsListSnippets . " <C-R>=UltiSnips#ListSnippets()<cr>"
    exec "snoremap <silent> " . g:UltiSnipsListSnippets . " <Esc>:call UltiSnips#ListSnippets()<cr>"

    snoremap <silent> <BS> <c-g>c
    snoremap <silent> <DEL> <c-g>c
    snoremap <silent> <c-h> <c-g>c
endf

function! UltiSnips#map_keys#MapInnerKeys()
    if g:UltiSnipsExpandTrigger != g:UltiSnipsJumpForwardTrigger
        exec "inoremap <buffer> <silent> " . g:UltiSnipsJumpForwardTrigger . " <C-R>=UltiSnips#JumpForwards()<cr>"
        exec "snoremap <buffer> <silent> " . g:UltiSnipsJumpForwardTrigger . " <Esc>:call UltiSnips#JumpForwards()<cr>"
    endif
    exec "inoremap <buffer> <silent> " . g:UltiSnipsJumpBackwardTrigger . " <C-R>=UltiSnips#JumpBackwards()<cr>"
    exec "snoremap <buffer> <silent> " . g:UltiSnipsJumpBackwardTrigger . " <Esc>:call UltiSnips#JumpBackwards()<cr>"
endf

function! UltiSnips#map_keys#RestoreInnerKeys()
    if g:UltiSnipsExpandTrigger != g:UltiSnipsJumpForwardTrigger
        exec "iunmap <buffer> " . g:UltiSnipsJumpForwardTrigger
        exec "sunmap <buffer> " . g:UltiSnipsJumpForwardTrigger
    endif
    exec "iunmap <buffer> " . g:UltiSnipsJumpBackwardTrigger
    exec "sunmap <buffer> " . g:UltiSnipsJumpBackwardTrigger
endf
