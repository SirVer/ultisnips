" Syntax highlighting for snippet files (used for UltiSnips.vim)
" Revision: 26/03/11 19:53:33

if exists("b:current_syntax")
  finish
endif

" Embedded Syntaxes {{{1

syntax include @Python syntax/python.vim
unlet b:current_syntax
syntax include @Viml syntax/vim.vim
unlet b:current_syntax
syntax include @Shell syntax/sh.vim
unlet b:current_syntax

" Syntax definitions {{{1

" Comments {{{2

syn match snipComment "^#.*" contains=snipTODO display
syn keyword snipTODO contained display FIXME NOTE NOTES TODO XXX

" Miscellaneous {{{2

syn match snipDocString '"[^"]*"$'
syn match snipString '"[^"]*"'
syn match snipTabsOnly "^\t\+$"
syn match snipLeadingSpaces "^\t* \+"

syn match snipKeyword "\(\<\(end\)\?\(snippet\|global\)\>\)\|extends\|clearsnippets\|priority" contained

" Extends {{{2

syn match snipExtends "^extends\%(\s.*\|$\)" contains=snipExtendsKeyword display
syn match snipExtendsKeyword "^extends" contained display

" Definitions {{{2

" snippet {{{3

syn region snipSnippet start="^snippet\_s" end="^endsnippet\s*$" contains=snipSnippetHeader fold keepend
syn match snipSnippetHeader "^.*$" nextgroup=snipSnippetBody skipnl contained contains=snipSnippetHeaderKeyword
syn match snipSnippetHeaderKeyword "^snippet" contained nextgroup=snipSnippetTrigger
syn region snipSnippetBody start="\_." end="^\zeendsnippet\s*$" contained contains=snipTabsOnly,snipLeadingSpaces,snipCommand,snipVarExpansion,snipVar,snipVisual nextgroup=snipSnippetFooter
syn match snipSnippetFooter "^endsnippet.*" contained contains=snipSnippetFooterKeyword
syn match snipSnippetFooterKeyword "^endsnippet" contained

" Command substitution {{{4

syn region snipCommand keepend matchgroup=snipCommandDelim start="`" skip="\\[{}\\$`]" end="`" contains=snipPythonCommand,snipVimLCommand,snipShellCommand
syn region snipShellCommand start="\ze\_." skip="\\[{}\\$`]" end="\ze`" contained contains=@Shell
syn region snipPythonCommand matchgroup=snipPythonCommandP start="`\@<=!p\_s" skip="\\[{}\\$`]" end="\ze`" contained contains=@Python
syn region snipVimLCommand matchgroup=snipVimLCommandV start="`\@<=!v\_s" skip="\\[{}\\$`]" end="\ze`" contained contains=@Viml

" Variables {{{4

syn match snipVar "\$\d*" contained
syn region snipVisual matchgroup=Define start="\${VISUAL" end="}" contained
syn region snipVarExpansion matchgroup=Define start="\${\d*" end="}" contained contains=snipVar,snipVarExpansion,snipCommand

" global {{{3

syn match snipGlobalStart "^global.*" contained contains=snipKeyword,snipString
syn match snipGlobalEnd "^endglobal" contained contains=snipKeyword
syn region snipGlobal fold keepend start="^global" end="^endglobal" contains=snipGlobalStart,snipGlobalEnd,snipLeadingSpaces,snipTabsOnly,snipCommand,snipVarExpansion,snipVar,@Python

" priority {{{3

syn match snipPriority "^priority\%(\s.*\|$\)" contains=snipPriorityKeyword display
syn match snipPriorityKeyword "^priority" contained nextgroup=snipPriorityValue skipwhite display
syn match snipPriorityValue "-\?\d\+" contained display

" Snippt Clearing {{{2

syn match snipClear "^clearsnippets\%(\s.*\|$\)" contains=snipClearKeyword display
syn match snipClearKeyword "^clearsnippets" contained display

" Highlight groups {{{1

hi def link snipComment          Comment
hi def link snipLeadingSpaces    Error
hi def link snipString           String
hi def link snipDocString        String
hi def link snipTabsOnly         Error

hi def link snipKeyword          Keyword

hi def link snipExtendsKeyword   Keyword

hi def link snipSnippetHeaderKeyword snipKeyword
hi def link snipSnippetFooterKeyword snipKeyword

hi def link snipStart            Statement
hi def link snipEnd              snipStart

hi def link snipCommand          Special
hi def link snipCommandDelim     snipCommand
hi def link snipShellCommand     snipCommand
hi def link snipPythonCommand    snipCommand
hi def link snipVimLCommand      snipCommand
hi def link snipPythonCommandP   PreProc
hi def link snipVimLCommandV     PreProc

hi def link snipVar              StorageClass
hi def link snipVarExpansion     Normal
hi def link snipVisual           Normal
hi def link snipSnippet          Normal

hi def link snipGlobalStart      Statement
hi def link snipGlobalEnd        Statement
hi def link snipGlobal           Normal

hi def link snipPriorityKeyword  Keyword
hi def link snipPriorityValue    Number

hi def link snipClearKeyword     Keyword

" }}}1

let b:current_syntax = "snippets"
