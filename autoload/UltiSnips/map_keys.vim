" Defaults for the public `g:UltiSnips*` globals live in plugin/UltiSnips.vim
" so the Python module (which reads `g:UltiSnipsExpandTrigger` etc. at import
" time) finds them set regardless of the user's vimrc. See #1679.

function! UltiSnips#map_keys#MapKeys() abort
    if exists("g:UltiSnipsExpandOrJumpTrigger")
        exec "inoremap <silent> " . g:UltiSnipsExpandOrJumpTrigger . " <C-R>=UltiSnips#ExpandSnippetOrJump()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandOrJumpTrigger . " <Esc>:call UltiSnips#ExpandSnippetOrJump()<cr>"
    elseif exists("g:UltiSnipsJumpOrExpandTrigger")
        exec "inoremap <silent> " . g:UltiSnipsJumpOrExpandTrigger . " <C-R>=UltiSnips#JumpOrExpandSnippet()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsJumpOrExpandTrigger . " <Esc>:call UltiSnips#JumpOrExpandSnippet()<cr>"
    elseif g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger
        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippetOrJump()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippetOrJump()<cr>"
    else
        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippet()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippet()<cr>"
    endif
    exec "xnoremap <silent> " . g:UltiSnipsExpandTrigger. " :call UltiSnips#SaveLastVisualSelection()<cr>gv\"_s"
    if len(g:UltiSnipsListSnippets) > 0
       exec "inoremap <silent> " . g:UltiSnipsListSnippets . " <C-R>=UltiSnips#ListSnippets()<cr>"
       exec "snoremap <silent> " . g:UltiSnipsListSnippets . " <Esc>:call UltiSnips#ListSnippets()<cr>"
    endif

    snoremap <silent> <BS> <c-g>"_c
    snoremap <silent> <DEL> <c-g>"_c
    snoremap <silent> <c-h> <c-g>"_c
    snoremap <c-r> <c-g>"_c<c-r>
endf
