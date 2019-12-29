call plug#begin('~/.vim_plugged')

Plug '/src/UltiSnips'
Plug 'honza/vim-snippets'

let g:UltiSnipsExpandTrigger="<tab>"

" Weird choices for triggers, but I wanted something that is rarely typed and
" never eaten by the shell.
let g:UltiSnipsListSnippets="9"
let g:UltiSnipsJumpForwardTrigger="2"
let g:UltiSnipsJumpBackwardTrigger="1"

let g:UltiSnipsEditSplit="vertical"

call plug#end()
