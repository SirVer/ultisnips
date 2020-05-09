" Syntax highlighting for snippet files (used for UltiSnips.vim)
" Revision: 26/03/11 19:53:33

if exists("b:current_syntax")
  finish
endif

if expand("%:p:h") =~ "snippets" && search("^endsnippet", "nw") == 0
            \ && !exists("b:ultisnips_override_snipmate")
    " this appears to be a snipmate file
    " It's in a directory called snippets/ and there's no endsnippet keyword
    " anywhere in the file.
    source <sfile>:h/snippets_snipmate.vim
    finish
endif

" Embedded Syntaxes {{{1

try
   syntax include @Python syntax/python.vim
   unlet b:current_syntax
   syntax include @Viml syntax/vim.vim
   unlet b:current_syntax
   syntax include @Shell syntax/sh.vim
   unlet b:current_syntax
catch /E403/
   " Ignore errors about syntax files that can't be loaded more than once
endtry

" Syntax definitions {{{1

" Comments {{{2

syn match snipComment "^#.*" contains=snipTODO,@Spell display
syn keyword snipTODO contained display FIXME NOTE NOTES TODO XXX

" Errors {{{2

syn match snipLeadingSpaces "^\t* \+" contained

" Extends {{{2

syn match snipExtends "^extends\%(\s.*\|$\)" contains=snipExtendsKeyword display
syn match snipExtendsKeyword "^extends" contained display

" Definitions {{{2

" snippet {{{3

syn region snipSnippet start="^snippet\_s" end="^endsnippet\s*$" contains=snipSnippetHeader fold keepend
syn match snipSnippetHeader "^.*$" nextgroup=snipSnippetBody,snipSnippetFooter skipnl contained contains=snipSnippetHeaderKeyword
syn match snipSnippetHeaderKeyword "^snippet" contained nextgroup=snipSnippetTrigger skipwhite
syn region snipSnippetBody start="\_." end="^\zeendsnippet\s*$" contained nextgroup=snipSnippetFooter contains=snipLeadingSpaces,@snipTokens
syn match snipSnippetFooter "^endsnippet.*" contained contains=snipSnippetFooterKeyword
syn match snipSnippetFooterKeyword "^endsnippet" contained

" The current parser is a bit lax about parsing. For example, given this:
"   snippet foo"bar"
" it treats `foo"bar"` as the trigger. But with this:
"   snippet foo"bar baz"
" it treats `foo` as the trigger and "bar baz" as the description.
" I think this is an accident. Instead, we'll assume the description must
" be surrounded by spaces. That means we'll treat
"   snippet foo"bar"
" as a trigger `foo"bar"` and
"   snippet foo"bar baz"
" as an attempted multiword snippet `foo"bar baz"` that is invalid.
" NB: UltiSnips parses right-to-left, which Vim doesn't support, so that makes
" the following patterns very complicated.
syn match snipSnippetTrigger "\S\+" contained nextgroup=snipSnippetDocString,snipSnippetTriggerInvalid skipwhite
" We want to match a trailing " as the start of a doc comment, but we also
" want to allow for using " as the delimiter in a multiword/pattern snippet.
" So we have to define this twice, once in the general case that matches a
" trailing " as the doc comment, and once for the case of the multiword
" delimiter using " that has more constraints
syn match snipSnippetTrigger ,".\{-}"\ze\%(\s\+"\%(\s*\S\)\@=[^"]*\%("\s\+[^"[:space:]]\+\|"\)\=\)\=\s*$, contained nextgroup=snipSnippetDocString skipwhite
syn match snipSnippetTrigger ,\%(\(\S\).\{-}\1\|\S\+\)\ze\%(\s\+"[^"]*\%("\s\+\%("[^"]\+"\s\+[^"[:space:]]*e[^"[:space:]]*\)\|"\)\=\)\=\s*$, contained nextgroup=snipSnippetDocContextString skipwhite
syn match snipSnippetTrigger ,\([^"[:space:]]\).\{-}\1\%(\s*$\)\@!\ze\%(\s\+"[^"]*\%("\s\+\%("[^"]\+"\s\+[^"[:space:]]*e[^"[:space:]]*\|[^"[:space:]]\+\)\|"\)\=\)\=\s*$, contained nextgroup=snipSnippetDocString skipwhite
syn match snipSnippetTriggerInvalid ,\S\@=.\{-}\S\ze\%(\s\+"[^"]*\%("\s\+[^"[:space:]]\+\s*\|"\s*\)\=\|\s*\)$, contained nextgroup=snipSnippetDocString skipwhite
syn match snipSnippetDocString ,"[^"]*", contained nextgroup=snipSnippetOptions skipwhite
syn match snipSnippetDocContextString ,"[^"]*", contained nextgroup=snipSnippetContext skipwhite
syn match snipSnippetContext ,"[^"]\+", contained skipwhite contains=snipSnippetContextP
syn region snipSnippetContextP start=,"\@<=., end=,\ze", contained contains=@Python nextgroup=snipSnippetOptions skipwhite keepend
syn match snipSnippetOptions ,\S\+, contained contains=snipSnippetOptionFlag
syn match snipSnippetOptionFlag ,[biwrtsmxAe], contained

" Command substitution {{{4

syn region snipCommand keepend matchgroup=snipCommandDelim start="`" skip="\\[{}\\$`]" end="`" contained contains=snipPythonCommand,snipVimLCommand,snipShellCommand,snipCommandSyntaxOverride
syn region snipShellCommand start="\ze\_." skip="\\[{}\\$`]" end="\ze`" contained contains=@Shell
syn region snipPythonCommand matchgroup=snipPythonCommandP start="`\@<=!p\_s" skip="\\[{}\\$`]" end="\ze`" contained contains=@Python
syn region snipVimLCommand matchgroup=snipVimLCommandV start="`\@<=!v\_s" skip="\\[{}\\$`]" end="\ze`" contained contains=@Viml
syn cluster snipTokens add=snipCommand
syn cluster snipTabStopTokens add=snipCommand

" unfortunately due to the balanced braces parsing of commands, if a { occurs
" in the command, we need to prevent the embedded syntax highlighting.
" Otherwise, we can't track the balanced braces properly.

syn region snipCommandSyntaxOverride start="\%(\\[{}\\$`]\|\_[^`"{]\)*\ze{" skip="\\[{}\\$`]" end="\ze`" contained contains=snipBalancedBraces transparent

" Tab Stops {{{4

syn match snipEscape "\\[{}\\$`]" contained
syn cluster snipTokens add=snipEscape
syn cluster snipTabStopTokens add=snipEscape

syn match snipMirror "\$\d\+" contained
syn cluster snipTokens add=snipMirror
syn cluster snipTabStopTokens add=snipMirror

syn region snipTabStop matchgroup=snipTabStop start="\${\d\+[:}]\@=" end="}" contained contains=snipTabStopDefault extend
syn region snipTabStopDefault matchgroup=snipTabStop start=":" skip="\\[{}]" end="\ze}" contained contains=snipTabStopEscape,snipBalancedBraces,@snipTabStopTokens keepend
syn match snipTabStopEscape "\\[{}]" contained
syn region snipBalancedBraces start="{" end="}" contained transparent extend
syn cluster snipTokens add=snipTabStop
syn cluster snipTabStopTokens add=snipTabStop

syn region snipVisual matchgroup=snipVisual start="\${VISUAL[:}/]\@=" end="}" contained contains=snipVisualDefault,snipTransformationPattern extend
syn region snipVisualDefault matchgroup=snipVisual start=":" end="\ze[}/]" contained contains=snipTabStopEscape nextgroup=snipTransformationPattern
syn cluster snipTokens add=snipVisual
syn cluster snipTabStopTokens add=snipVisual

syn region snipTransformation matchgroup=snipTransformation start="\${\d\/\@=" end="}" contained contains=snipTransformationPattern
syn region snipTransformationPattern matchgroup=snipTransformationPatternDelim start="/" end="\ze/" contained contains=snipTransformationEscape nextgroup=snipTransformationReplace skipnl
syn region snipTransformationReplace matchgroup=snipTransformationPatternDelim start="/" end="/" contained contains=snipTransformationEscape nextgroup=snipTransformationOptions skipnl
syn region snipTransformationOptions start="\ze[^}]" end="\ze}" contained contains=snipTabStopEscape
syn match snipTransformationEscape "\\/" contained
syn cluster snipTokens add=snipTransformation
syn cluster snipTabStopTokens add=snipTransformation

" global {{{3

" Generic (non-Python) {{{4

syn region snipGlobal start="^global\_s" end="^\zeendglobal\s*$" contains=snipGlobalHeader nextgroup=snipGlobalFooter fold keepend
syn match snipGlobalHeader "^.*$" nextgroup=snipGlobalBody,snipGlobalFooter skipnl contained contains=snipGlobalHeaderKeyword
syn region snipGlobalBody start="\_." end="^\zeendglobal\s*$" contained contains=snipLeadingSpaces

" Python (!p) {{{4

syn region snipGlobal start=,^global\s\+!p\%(\s\+"[^"]*\%("\s\+[^"[:space:]]\+\|"\)\=\)\=\s*$, end=,^\zeendglobal\s*$, contains=snipGlobalPHeader nextgroup=snipGlobalFooter fold keepend
syn match snipGlobalPHeader "^.*$" nextgroup=snipGlobalPBody,snipGlobalFooter skipnl contained contains=snipGlobalHeaderKeyword
syn match snipGlobalHeaderKeyword "^global" contained nextgroup=snipSnippetTrigger skipwhite
syn region snipGlobalPBody start="\_." end="^\zeendglobal\s*$" contained contains=@Python

" Common {{{4

syn match snipGlobalFooter "^endglobal.*" contained contains=snipGlobalFooterKeyword
syn match snipGlobalFooterKeyword "^endglobal" contained

" priority {{{3

syn match snipPriority "^priority\%(\s.*\|$\)" contains=snipPriorityKeyword display
syn match snipPriorityKeyword "^priority" contained nextgroup=snipPriorityValue skipwhite display
syn match snipPriorityValue "-\?\d\+" contained display

" context {{{3

syn match snipContext "^context.*$" contains=snipContextKeyword display skipwhite
syn match snipContextKeyword "context" contained nextgroup=snipContextValue skipwhite display
syn match snipContextValue '"[^"]*"' contained contains=snipContextValueP
syn region snipContextValueP start=,"\@<=., end=,\ze", contained contains=@Python skipwhite keepend

" Actions {{{3

syn match snipAction "^\%(pre_expand\|post_expand\|post_jump\).*$" contains=snipActionKeyword display skipwhite
syn match snipActionKeyword "\%(pre_expand\|post_expand\|post_jump\)" contained nextgroup=snipActionValue skipwhite display
syn match snipActionValue '"[^"]*"' contained contains=snipActionValueP
syn region snipActionValueP start=,"\@<=., end=,\ze", contained contains=@Python skipwhite keepend

" Snippt Clearing {{{2

syn match snipClear "^clearsnippets\%(\s.*\|$\)" contains=snipClearKeyword display
syn match snipClearKeyword "^clearsnippets" contained display

" Highlight groups {{{1

hi def link snipComment          Comment
hi def link snipTODO             Todo
hi def snipLeadingSpaces term=reverse ctermfg=15 ctermbg=4 gui=reverse guifg=#dc322f

hi def link snipKeyword          Keyword

hi def link snipExtendsKeyword   snipKeyword

hi def link snipSnippetHeaderKeyword snipKeyword
hi def link snipSnippetFooterKeyword snipKeyword

hi def link snipSnippetTrigger        Identifier
hi def link snipSnippetTriggerInvalid Error
hi def link snipSnippetDocString      String
hi def link snipSnippetDocContextString String
hi def link snipSnippetOptionFlag     Special

hi def link snipGlobalHeaderKeyword  snipKeyword
hi def link snipGlobalFooterKeyword  snipKeyword

hi def link snipCommand          Special
hi def link snipCommandDelim     snipCommand
hi def link snipShellCommand     snipCommand
hi def link snipVimLCommand      snipCommand
hi def link snipPythonCommandP   PreProc
hi def link snipVimLCommandV     PreProc
hi def link snipSnippetContext   String
hi def link snipContext          String
hi def link snipAction           String

hi def link snipEscape                     Special
hi def link snipMirror                     StorageClass
hi def link snipTabStop                    Define
hi def link snipTabStopDefault             String
hi def link snipTabStopEscape              Special
hi def link snipVisual                     snipTabStop
hi def link snipVisualDefault              snipTabStopDefault
hi def link snipTransformation             snipTabStop
hi def link snipTransformationPattern      String
hi def link snipTransformationPatternDelim Operator
hi def link snipTransformationReplace      String
hi def link snipTransformationEscape       snipEscape
hi def link snipTransformationOptions      Operator

hi def link snipContextKeyword  Keyword

hi def link snipPriorityKeyword  Keyword
hi def link snipPriorityValue    Number

hi def link snipActionKeyword  Keyword

hi def link snipClearKeyword     Keyword

" }}}1

let b:current_syntax = "snippets"
