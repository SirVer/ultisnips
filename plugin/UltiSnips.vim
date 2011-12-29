" File: UltiSnips.vim
" Author: Holger Rapp <SirVer@gmx.de>
" Description: The Ultimate Snippets solution for Vim
" Last Modified: July 21, 2009
"
" Testing Info: {{{
"   See directions at the top of the test.py script located one 
"   directory above this file.
" }}}

if exists('did_UltiSnips_vim') || &cp || version < 700 || !has("python")
    finish
endif

" Global Variables {{{

" The trigger used to expand a snippet.
" NOTE: expansion and forward jumping can, but needn't be the same trigger
if !exists("g:UltiSnipsExpandTrigger")
    let g:UltiSnipsExpandTrigger = "<tab>"
endif

" The trigger used to display all triggers that could possible 
" match in the current position.
if !exists("g:UltiSnipsListSnippets")
    let g:UltiSnipsListSnippets = "<c-tab>"
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

" Should UltiSnips unmap select mode mappings automagically?
if !exists("g:UltiSnipsRemoveSelectModeMappings")
    let g:UltiSnipsRemoveSelectModeMappings = 1
end

" If UltiSnips should remove Mappings, which should be ignored
if !exists("g:UltiSnipsMappingsToIgnore")
    let g:UltiSnipsMappingsToIgnore = []
endif

" UltiSnipsEdit will use this variable to decide if a new window
" is opened when editing. default is "normal", allowed are also
" "vertical", "horizontal"
if !exists("g:UltiSnipsEditSplit")
    let g:UltiSnipsEditSplit = 'normal'
endif

" A list of directory names that are searched for snippets. 
if !exists("g:UltiSnipsSnippetDirectories")
    let g:UltiSnipsSnippetDirectories = [ "UltiSnips" ]
endif
" }}}

"" Global Commands {{{
function! UltiSnipsEdit(...)
    if a:0 == 1 && a:1 != ''
        let type = a:1
    else
        python vim.command("let type = '%s'" % UltiSnips_Manager.filetype)
    endif

    python vim.command("let file = '%s'" % UltiSnips_Manager.file_to_edit(vim.eval("type")))

    let mode = 'e'
    if exists('g:UltiSnipsEditSplit')
        if g:UltiSnipsEditSplit == 'vertical'
            let mode = 'vs'
        elseif g:UltiSnipsEditSplit == 'horizontal'
            let mode = 'sp'
        endif
    endif
    exe ':'.mode.' '.file
endfunction

" edit snippets, default of current file type or the specified type
command! -nargs=? UltiSnipsEdit :call UltiSnipsEdit(<q-args>)

"" }}}

"" FUNCTIONS {{{
function! CompensateForPUM()
    """ The CursorMovedI event is not triggered while the popup-menu is visible,
    """ and it's by this event that UltiSnips updates its vim-state. The fix is
    """ to explicitly check for the presence of the popup menu, and update
    """ the vim-state accordingly.
    if pumvisible()
        py UltiSnips_Manager.cursor_moved()
    endif
endfunction

function! UltiSnips_ExpandSnippet()
    py UltiSnips_Manager.expand()
    return ""
endfunction

function! UltiSnips_ExpandSnippetOrJump()
    call CompensateForPUM()
    py UltiSnips_Manager.expand_or_jump()
    return ""
endfunction

function! UltiSnips_ListSnippets()
    py UltiSnips_Manager.list_snippets()
    return ""
endfunction

function! UltiSnips_JumpBackwards()
    call CompensateForPUM()
    py UltiSnips_Manager.jump_backwards()
    return ""
endfunction

function! UltiSnips_JumpForwards()
    call CompensateForPUM()
    py UltiSnips_Manager.jump_forwards()
    return ""
endfunction

function! UltiSnips_AddSnippet(trigger, value, descr, options, ...)
    " Takes the same arguments as SnippetManager.add_snippet:
    " (trigger, value, descr, options, ft = "all", globals = None)
py << EOB
args = vim.eval("a:000")
trigger = vim.eval("a:trigger")
value = vim.eval("a:value")
descr = vim.eval("a:descr")
options = vim.eval("a:options")

UltiSnips_Manager.add_snippet(trigger, value, descr, options, *args)
EOB
    return ""
endfunction

function! UltiSnips_Anon(value, ...)
    " Takes the same arguments as SnippetManager.expand_anon:
    " (value, trigger="", descr="", options="", globals = None)
py << EOB
args = vim.eval("a:000")
value = vim.eval("a:value")
UltiSnips_Manager.expand_anon(value, *args)
EOB
    return ""
endfunction

function! UltiSnips_MapKeys()
    " Map the keys correctly
    if g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger
        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips_ExpandSnippetOrJump()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips_ExpandSnippetOrJump()<cr>"
    else
        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips_ExpandSnippet()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips_ExpandSnippet()<cr>"
        exec "inoremap <silent> " . g:UltiSnipsJumpForwardTrigger  . " <C-R>=UltiSnips_JumpForwards()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsJumpForwardTrigger  . " <Esc>:call UltiSnips_JumpForwards()<cr>"
    endif
    exec "inoremap <silent> " . g:UltiSnipsJumpBackwardTrigger . " <C-R>=UltiSnips_JumpBackwards()<cr>"
    exec "snoremap <silent> " . g:UltiSnipsJumpBackwardTrigger . " <Esc>:call UltiSnips_JumpBackwards()<cr>"
    exec "inoremap <silent> " . g:UltiSnipsListSnippets . " <C-R>=UltiSnips_ListSnippets()<cr>"
    exec "snoremap <silent> " . g:UltiSnipsListSnippets . " <Esc>:call UltiSnips_ListSnippets()<cr>"

    " Do not remap this.
    snoremap <silent> <BS> <Esc>:py  UltiSnips_Manager.backspace_while_selected()<cr>
endf

function! UltiSnips_CursorMoved()
    py UltiSnips_Manager.cursor_moved()
endf
function! UltiSnips_EnteredInsertMode()
    py UltiSnips_Manager.entered_insert_mode()
endf
function! UltiSnips_LeavingWindow()
    py UltiSnips_Manager.leaving_window()
endf
" }}}

"" STARTUP CODE {{{

" Expand our path
python << EOF
import vim, os, sys

new_path = vim.eval('expand("<sfile>:h")')
sys.path.append(new_path)

from UltiSnips import UltiSnips_Manager
UltiSnips_Manager.expand_trigger = vim.eval("g:UltiSnipsExpandTrigger")
UltiSnips_Manager.forward_trigger = vim.eval("g:UltiSnipsJumpForwardTrigger")
UltiSnips_Manager.backward_trigger = vim.eval("g:UltiSnipsJumpBackwardTrigger")
EOF

au CursorMovedI * call UltiSnips_CursorMoved()
au InsertEnter * call UltiSnips_EnteredInsertMode()
au WinLeave * call UltiSnips_LeavingWindow()

call UltiSnips_MapKeys()

let did_UltiSnips_vim=1

" }}}
" vim: ts=8 sts=4 sw=4
