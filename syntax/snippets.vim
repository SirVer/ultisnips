" Syntax highlighting for snippet files (used for UltiSnips.vim)
" Revision: 26/03/11 19:53:33

if exists("b:current_syntax")
  finish
endif

syntax include @Python syntax/python.vim
syntax include @Viml syntax/vim.vim

" global matches
syn match snipComment "^#.*" contains=snipTODO
syn keyword snipTODO FIXME NOTE NOTES TODO XXX contained

syn match snipDocString '"[^"]*"$'
syn match snipString '"[^"]*"'
syn match snipTabsOnly "^\t\+$"

syn match snipKeyword "\(\<\(end\)\?\(snippet\|global\)\>\)\|extends\|clearsnippets" contained

" extends definitions
syn match snipExtends "^extends.*" contains=snipKeyword

" snippet definitions
syn match snipStart "^snippet.*" contained contains=snipKeyword,snipDocString
syn match snipEnd "^endsnippet" contained contains=snipKeyword
syn region snipCommand contained keepend start="`" end="`" contains=snipPythonCommand,snipVimLCommand
syn region snipPythonCommand contained keepend start="`!p" end="`" contained contains=@Python
syn region snipVimLCommand contained keepend start="`!v" end="`" contained contains=@Viml
syn match snipVar "\$\d*" contained
syn region snipVisual matchgroup=Define start="\${VISUAL" end="}" contained
syn region snipVarExpansion matchgroup=Define start="\${\d*" end="}" contained contains=snipVar,snipVarExpansion,snipCommand
syn region snippet fold keepend start="^snippet" end="^endsnippet" contains=snipStart,snipEnd,snipTabsOnly,snipCommand,snipVarExpansion,snipVar,snipVisual

" global definitions
syn match snipGlobalStart "^global.*" contained contains=snipKeyword,snipString
syn match snipGlobalEnd "^endglobal" contained contains=snipKeyword
syn region snipGlobal fold keepend start="^global" end="^endglobal" contains=snipGlobalStart,snipGlobalEnd,snipTabsOnly,snipCommand,snipVarExpansion,snipVar,@Python

" snippet clearing
syn match snipClear "^clearsnippets"

" highlighting rules

hi link snipComment      Comment
hi link snipString       String
hi link snipDocString    String
hi link snipTabsOnly     Error

hi link snipKeyword      Keyword

hi link snipExtends      Statement

hi link snipStart        Statement
hi link snipEnd          Statement
hi link snipCommand      Special
hi link snipVar          StorageClass
hi link snipVarExpansion Normal
hi link snipVisual       Normal
hi link snippet          Normal

hi link snipGlobalStart  Statement
hi link snipGlobalEnd    Statement
hi link snipGlobal       Normal

hi link snipClear        Statement

let b:current_syntax = "snippet"
