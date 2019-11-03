" Syntax highlighting variant used for snipmate snippets files
" The snippets.vim file sources this if it wants snipmate mode

if exists("b:current_syntax")
    finish
endif

" Embedded syntaxes {{{1

" Re-include the original file so we can share some of its definitions
let b:ultisnips_override_snipmate = 1
syn include <sfile>:h/snippets.vim
unlet b:current_syntax
unlet b:ultisnips_override_snipmate

syn cluster snipTokens contains=snipEscape,snipVisual,snipTabStop,snipMirror,snipmateCommand
syn cluster snipTabStopTokens contains=snipVisual,snipMirror,snipEscape,snipmateCommand

" Syntax definitions {{{1

syn match snipmateComment "^#.*"

syn match snipmateExtends "^extends\%(\s.*\|$\)" contains=snipExtendsKeyword display

syn region snipmateSnippet start="^snippet\ze\%(\s\|$\)" end="^\ze[^[:tab:]]" contains=snipmateSnippetHeader keepend
syn match snipmateSnippetHeader "^.*" contained contains=snipmateKeyword nextgroup=snipmateSnippetBody skipnl skipempty
syn match snipmateKeyword "^snippet\ze\%(\s\|$\)" contained nextgroup=snipmateTrigger skipwhite
syn match snipmateTrigger "\S\+" contained nextgroup=snipmateDescription skipwhite
syn match snipmateDescription "\S.*" contained
syn region snipmateSnippetBody start="^\t" end="^\ze[^[:tab:]]" contained contains=@snipTokens

syn region snipmateCommand keepend matchgroup=snipCommandDelim start="`" skip="\\[{}\\$`]" end="`" contained contains=snipCommandSyntaxOverride,@Viml

" Highlight groups {{{1

hi def link snipmateComment snipComment

hi def link snipmateSnippet snipSnippet
hi def link snipmateKeyword snipKeyword
hi def link snipmateTrigger snipSnippetTrigger
hi def link snipmateDescription snipSnippetDocString

hi def link snipmateCommand snipCommand

" }}}1

let b:current_syntax = "snippets"
