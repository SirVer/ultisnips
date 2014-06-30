" Syntax highlighting for snippet files (used for UltiSnips.vim)
" Revision: 26/03/11 19:53:33

if exists("b:current_syntax")
  finish
endif

syntax include @Python syntax/python.vim
unlet b:current_syntax
syntax include @Viml syntax/vim.vim
unlet b:current_syntax

" global matches
syn match snipComment "^#.*" contains=snipTODO
syn keyword snipTODO FIXME NOTE NOTES TODO XXX contained

syn match snipDocString '"[^"]*"$'
syn match snipString '"[^"]*"'
syn match snipTabsOnly "^\t\+$"
syn match snipLeadingSpaces "^\t* \+"

syn match snipKeyword "\(\<\(end\)\?\(snippet\|global\)\>\)\|extends\|clearsnippets\|priority" contained

" extends definitions
syn match snipExtends "^extends.*" contains=snipKeyword

" snippet definitions
syn match snipStart "^snippet.*" contained contains=snipKeyword,snipDocString
syn match snipEnd "^endsnippet" contained contains=snipKeyword
syn region snipCommand keepend start="`" skip="\\[{}\\$`]" end="`" contains=snipPythonCommand,snipVimLCommand
syn region snipPythonCommand keepend start="`!p" skip="\\[{}\\$`]" end="`" contained contains=@Python
syn region snipVimLCommand keepend start="`!v" skip="\\[{}\\$`]" end="`" contained contains=@Viml
syn match snipVar "\$\d*" contained
syn region snipVisual matchgroup=Define start="\${VISUAL" end="}" contained
syn region snipVarExpansion matchgroup=Define start="\${\d*" end="}" contained contains=snipVar,snipVarExpansion,snipCommand
syn region snippet fold keepend start="^snippet" end="^endsnippet" contains=snipStart,snipEnd,snipTabsOnly,snipLeadingSpaces,snipCommand,snipVarExpansion,snipVar,snipVisual

" global definitions
syn match snipGlobalStart "^global.*" contained contains=snipKeyword,snipString
syn match snipGlobalEnd "^endglobal" contained contains=snipKeyword
syn region snipGlobal fold keepend start="^global" end="^endglobal" contains=snipGlobalStart,snipGlobalEnd,snipLeadingSpaces,snipTabsOnly,snipCommand,snipVarExpansion,snipVar,@Python

" snippet clearing
syn match snipClear "^clearsnippets"
syn match snipPriority "^priority"

" highlighting rules

hi def link snipComment          Comment
hi def link snipLeadingSpaces    Error
hi def link snipString           String
hi def link snipDocString        String
hi def link snipTabsOnly         Error

hi def link snipKeyword          Keyword

hi def link snipExtends          Statement

hi def link snipStart            Statement
hi def link snipEnd              snipStart
hi def link snipCommand          Special
hi def link snipPythonCommand    snipCommand
hi def link snipVimLCommand      snipCommand
hi def link snipVar              StorageClass
hi def link snipVarExpansion     Normal
hi def link snipVisual           Normal
hi def link snippet              Normal

hi def link snipGlobalStart      Statement
hi def link snipGlobalEnd        Statement
hi def link snipGlobal           Normal

hi def link snipClear            Statement
hi def link snipPriority         Statement

let b:current_syntax = "snippets"
