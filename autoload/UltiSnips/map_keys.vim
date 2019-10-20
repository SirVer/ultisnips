if exists("b:did_autoload_ultisnips_map_keys") || !exists("g:_uspy")
   finish
endif
let b:did_autoload_ultisnips_map_keys = 1

" The trigger used to expand a snippet.
" NOTE: expansion and forward jumping can, but needn't be the same trigger
if !exists("g:UltiSnipsExpandTrigger")
    let g:UltiSnipsExpandTrigger = "<tab>"
endif

" The trigger used to display all triggers that could possible
" match in the current position. Use empty to disable.
if !exists("g:UltiSnipsListSnippets")
    let g:UltiSnipsListSnippets = "<c-tab>"
endif

" The trigger used to jump forward to the next placeholder.
" NOTE: expansion and forward jumping can be the same trigger.
if !exists("g:UltiSnipsJumpForwardTrigger")
    let g:UltiSnipsJumpForwardTrigger = "<c-j>"
endif

" The trigger to jump backward inside a snippet
if !exists("g:UltiSnipsJumpBackwardTrigger")
    let g:UltiSnipsJumpBackwardTrigger = "<c-k>"
endif

" Should UltiSnips unmap select mode mappings automagically?
if !exists("g:UltiSnipsRemoveSelectModeMappings")
    let g:UltiSnipsRemoveSelectModeMappings = 1
end

" If UltiSnips should remove Mappings, which should be ignored
if !exists("g:UltiSnipsMappingsToIgnore")
    let g:UltiSnipsMappingsToIgnore = []
endif

" UltiSnipsEdit will use this variable to decide if a new window
" is opened when editing. default is "normal", allowed are also
" "tabdo", "vertical", "horizontal", and "context".
if !exists("g:UltiSnipsEditSplit")
    let g:UltiSnipsEditSplit = 'normal'
endif

" A list of directory names that are searched for snippets.
if !exists("g:UltiSnipsSnippetDirectories")
    let g:UltiSnipsSnippetDirectories = [ "UltiSnips" ]
endif

" Enable or Disable snipmate snippet expansion.
if !exists("g:UltiSnipsEnableSnipMate")
    let g:UltiSnipsEnableSnipMate = 1
endif

inoremap <Plug>(UltiSnips#ExpandSnippetOrJump) <C-R>=UltiSnips#ExpandSnippetOrJump()<cr>
snoremap <Plug>(UltiSnips#ExpandSnippetOrJump) <Esc>:call UltiSnips#ExpandSnippetOrJump()<cr>
inoremap <Plug>(UltiSnips#ExpandSnippet) <C-R>=UltiSnips#ExpandSnippet()<cr>
snoremap <Plug>(UltiSnips#ExpandSnippet) <Esc>:call UltiSnips#ExpandSnippet()<cr>
xnoremap <Plug>(UltiSnips#SaveLastVisualSelection) :call UltiSnips#SaveLastVisualSelection()<cr>gvs
inoremap <Plug>(UltiSnips#ListSnippets) <C-R>=UltiSnips#ListSnippets()<cr>
snoremap <Plug>(UltiSnips#ListSnippets) <Esc>:call UltiSnips#ListSnippets()<cr>

function! UltiSnips#map_keys#MapKeys() abort
    if g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger
        exec "imap <silent> " . g:UltiSnipsExpandTrigger . " <Plug>(UltiSnips#ExpandSnippetOrJump)"
        exec "smap <silent> " . g:UltiSnipsExpandTrigger . " <Plug>(UltiSnips#ExpandSnippetOrJump)"
    else
        exec "imap <silent> " . g:UltiSnipsExpandTrigger . " <Plug>(UltiSnips#ExpandSnippet)"
        exec "smap <silent> " . g:UltiSnipsExpandTrigger . " <Plug>(UltiSnips#ExpandSnippet)"
    endif
    exec "xmap <silent> " . g:UltiSnipsExpandTrigger. " <Plug>(UltiSnips#SaveLastVisualSelection)"
    if len(g:UltiSnipsListSnippets) > 0
       exec "imap <silent> " . g:UltiSnipsListSnippets . " <Plug>(UltiSnips#ListSnippets)"
       exec "smap <silent> " . g:UltiSnipsListSnippets . " <Plug>(UltiSnips#ListSnippets)"
    endif

    snoremap <silent> <BS> <c-g>"_c
    snoremap <silent> <DEL> <c-g>"_c
    snoremap <silent> <c-h> <c-g>"_c
    snoremap <c-r> <c-g>"_c<c-r>
endf
