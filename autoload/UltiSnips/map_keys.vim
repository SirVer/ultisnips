call UltiSnips#bootstrap#Bootstrap()

function! UltiSnips#map_keys#MapKeys()
    if !exists('g:_uspy')
        " Do not map keys if bootstrapping failed (e.g. no Python).
        return
    endif

    " Map the keys correctly
    if g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger

        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippetOrJump()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippetOrJump()<cr>"
    else
        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippet()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippet()<cr>"
    endif
    exec "xnoremap <silent> " . g:UltiSnipsExpandTrigger. " :call UltiSnips#SaveLastVisualSelection()<cr>gvs"
    exec "inoremap <silent> " . g:UltiSnipsListSnippets . " <C-R>=UltiSnips#ListSnippets()<cr>"
    exec "snoremap <silent> " . g:UltiSnipsListSnippets . " <Esc>:call UltiSnips#ListSnippets()<cr>"

    snoremap <silent> <BS> <c-g>c
    snoremap <silent> <DEL> <c-g>c
    snoremap <silent> <c-h> <c-g>c
endf
