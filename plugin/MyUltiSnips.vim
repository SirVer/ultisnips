let g:UltiSnipsSnippetsDir = expand("~/.ultisnips")

"UltiSnips variables
" make YCM compatible with UltiSnips (using supertab)
let g:ycm_key_list_select_completion = ['<C-n>', '<Down>']
let g:ycm_key_list_previous_completion = ['<C-p>', '<Up>']
let g:SuperTabDefaultCompletionType = '<C-n>'
let g:UltiSnipsEditSplit='vertical'

" better key bindings for UltiSnipsExpandTrigger
let g:UltiSnipsExpandTrigger = "<tab>"
let g:UltiSnipsJumpForwardTrigger = "<tab>"
let g:UltiSnipsJumpBackwardTrigger = "<s-tab>"

if !isdirectory(UltiSnipsSnippetsDir)
	exec "!git clone https://github.com/countoren/ultisnips-snippets.git ".expand(UltiSnipsSnippetsDir)
endif

