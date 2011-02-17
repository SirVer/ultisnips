" Syntax highlighting for snippet files (used for UltiSnips.vim)

" global matches
syn match snipComment "^#.*"
syn match snipString '"[^"]*"'
syn match snipTabsOnly "^\t\+$"

syn match snipKeyword "\<\(end\)\?\(snippet\|global\)\>" contained

" snippet definitions
syn match snipStart "^snippet.*" contained contains=snipKeyword,snipString
syn match snipEnd "^endsnippet" contained contains=snipKeyword
syn region snippet fold keepend start="^snippet" end="^endsnippet" contains=snipStart,snipEnd,snipTabsOnly

" global definitions
syn match snipGlobalStart "^global.*" contained contains=snipKeyword,snipString
syn match snipGlobalEnd "^endglobal" contained contains=snipKeyword
syn region snipGlobal fold keepend start="^global" end="^endglobal" contains=snipGlobalStart,snipGlobalEnd,snipTabsOnly

" highlighting rules

hi link snipComment     Comment
hi link snipString      String
hi link snipTabsOnly    Error

hi link snipKeyword     Keyword

hi link snipStart       Statement
hi link snipEnd         Statement
hi link snippet         Normal

hi link snipGlobalStart Statement
hi link snipGlobalEnd   Statement
hi link snipGlobal      Normal
