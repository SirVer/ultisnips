" File: UltiSnips.vim
" Author: Holger Rapp <SirVer@gmx.de>
" Description: The Ultimate Snippets solution for Vim
" Last Modified: July 21, 2009
"
" Testing Info: {{{
"   Running vim + ultisnips with the absolute bar minimum settings inside a   screen session:
"     $ screen -S vim
"     $ vim -u NONE -U NONE -c ':set nocompatible' -c ':set runtimepath+=.'
"     $ ./test.py  # launch the testsuite
" }}}

if exists('did_UltiSnips_vim') || &cp || version < 700
	finish
endif

" Global Variables {{{

" The trigger used to expand a snippet.
" NOTE: expansion and forward jumping can, but needn't be the same trigger
if !exists("g:UltiSnipsExpandTrigger")
 let g:UltiSnipsExpandTrigger = "<tab>"
endif

" The trigger used to jump forward to the next placeholder. 
" NOTE: expansion and forward jumping can, but needn't be the same trigger
if !exists("g:UltiSnipsJumpForwardTrigger")
 let g:UltiSnipsJumpForwardTrigger = "<c-j>"
endif

" The trigger to jump backward inside a snippet
if !exists("g:UltiSnipsJumpBackwardTrigger")
 let g:UltiSnipsJumpBackwardTrigger = "<c-k>"
endif

" }}}

"" FUNCTIONS {{{
function! UltiSnips_ExpandSnippet()
 py UltiSnips_Manager.expand()
 return ""
endfunction

function! UltiSnips_ExpandSnippetOrJump()
 py UltiSnips_Manager.expand_or_jump()
 return ""
endfunction

function! UltiSnips_JumpBackwards()
 py UltiSnips_Manager.jump_backwards()
 return ""
endfunction

function! UltiSnips_JumpForwards()
 py UltiSnips_Manager.jump_forwards()
 return ""
endfunction

" }}}

"" STARTUP CODE {{{

" Expand our path
python << EOF
import vim, os, sys

for p in vim.eval("&runtimepath").split(','):
   dname = p + os.path.sep + "plugin"
   if os.path.exists(dname + os.path.sep + "UltiSnips"):
      if dname not in sys.path:
         sys.path.append(dname)
      break

from UltiSnips import UltiSnips_Manager
UltiSnips_Manager.expand_trigger = vim.eval("g:UltiSnipsExpandTrigger")
UltiSnips_Manager.forward_trigger = vim.eval("g:UltiSnipsJumpForwardTrigger")
UltiSnips_Manager.backward_trigger = vim.eval("g:UltiSnipsJumpBackwardTrigger")
EOF

" Map the keys correctly
if g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger
   exec "inoremap " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips_ExpandSnippetOrJump()<cr>"
   exec "snoremap " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips_ExpandSnippetOrJump()<cr>"
else
   exec "inoremap " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips_ExpandSnippet()<cr>"
   exec "snoremap " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips_ExpandSnippet()<cr>"
   exec "inoremap " . g:UltiSnipsJumpForwardTrigger  . " <C-R>=UltiSnips_JumpForwards()<cr>"
   exec "snoremap " . g:UltiSnipsJumpForwardTrigger  . " <Esc>:call UltiSnips_JumpForwards()<cr>"
endif
exec "inoremap " . g:UltiSnipsJumpBackwardTrigger . " <C-R>=UltiSnips_JumpBackwards()<cr>"
exec "snoremap " . g:UltiSnipsJumpBackwardTrigger . " <Esc>:call UltiSnips_JumpBackwards()<cr>"

" Do not remap this.
snoremap <BS> <Esc>:py  UltiSnips_Manager.backspace_while_selected()<cr>

au CursorMovedI * py UltiSnips_Manager.cursor_moved()
au InsertEnter * py UltiSnips_Manager.entered_insert_mode()
  
let did_UltiSnips_vim=1

" }}}
