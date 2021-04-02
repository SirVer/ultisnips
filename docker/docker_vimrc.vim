set hidden
call plug#begin('~/.vim/plugged')

Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug '/src/UltiSnips'

let g:UltiSnipsExpandTrigger="<tab>"

" Weird choices for triggers, but I wanted something that is rarely typed and
" never eaten by the shell.
let g:UltiSnipsListSnippets="9"
let g:UltiSnipsJumpForwardTrigger="<tab>"
let g:UltiSnipsJumpBackwardTrigger="1"

let g:UltiSnipsEditSplit="vertical"

call plug#end()
