" File: UltiSnips.vim
" Author: Holger Rapp <SirVer@gmx.de>
" Description: The Ultimate Snippets solution for Vim
"
" Testing Info: {{{
"   See directions at the top of the test.py script located one
"   directory above this file.
" }}}

if exists('did_UltiSnips_vim') || &cp || version < 700
    finish
endif

" Define dummy version of function called by autocommand setup in
" ftdetect/UltiSnips.vim.  If the function isn't defined (probably due to
" using a copy of vim without python support) it will cause an error anytime a
" new file is opened.
function! UltiSnips_FileTypeChanged()
endfunction

if !exists("g:UltiSnipsUsePythonVersion")
    let g:_uspy=":py3 "
    if !has("python3")
        if !has("python")
            if !exists("g:UltiSnipsNoPythonWarning")
                echo  "UltiSnips requires py >= 2.6 or any py3"
            endif
            finish
        endif
        let g:_uspy=":py "
    endif
    let g:UltiSnipsUsePythonVersion = "<tab>"
else
    if g:UltiSnipsUsePythonVersion == 2
        let g:_uspy=":py "
    else
        let g:_uspy=":py3 "
    endif
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

" Global Commands {{{
function! UltiSnipsEdit(...)
    if a:0 == 1 && a:1 != ''
        let type = a:1
    else
        exec g:_uspy "vim.command(\"let type = '%s'\" % UltiSnips_Manager.primary_filetype)"
    endif
    exec g:_uspy "vim.command(\"let file = '%s'\" % UltiSnips_Manager.file_to_edit(vim.eval(\"type\")))"

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
command! -nargs=? -complete=customlist,UltiSnipsFiletypeComplete UltiSnipsEdit
    \ :call UltiSnipsEdit(<q-args>)

" Global Commands {{{
function! UltiSnipsAddFiletypes(filetypes)
    exec g:_uspy "UltiSnips_Manager.add_buffer_filetypes('" . a:filetypes . ".all')"
    return ""
endfunction
command! -nargs=1 UltiSnipsAddFiletypes :call UltiSnipsAddFiletypes(<q-args>)

"" }}}

" FUNCTIONS {{{
function! CompensateForPUM()
    """ The CursorMovedI event is not triggered while the popup-menu is visible,
    """ and it's by this event that UltiSnips updates its vim-state. The fix is
    """ to explicitly check for the presence of the popup menu, and update
    """ the vim-state accordingly.
    if pumvisible()
        exec g:_uspy "UltiSnips_Manager.cursor_moved()"
    endif
endfunction
function! UltiSnips_ExpandSnippet()
    exec g:_uspy "UltiSnips_Manager.expand()"
    return ""
endfunction

function! UltiSnips_ExpandSnippetOrJump()
    call CompensateForPUM()
    exec g:_uspy "UltiSnips_Manager.expand_or_jump()"
    return ""
endfunction

function! UltiSnips_ListSnippets()
    exec g:_uspy "UltiSnips_Manager.list_snippets()"
    return ""
endfunction

function! UltiSnips_SnippetsInCurrentScope()
    let g:current_ulti_dict = {}
    exec g:_uspy "UltiSnips_Manager.list_snippets_dict()"
    return g:current_ulti_dict
endfunction

function! UltiSnips_SaveLastVisualSelection()
    exec g:_uspy "UltiSnips_Manager.save_last_visual_selection()"
    return ""
endfunction

function! UltiSnips_JumpBackwards()
    call CompensateForPUM()
    exec g:_uspy "UltiSnips_Manager.jump_backwards()"
    return ""
endfunction

function! UltiSnips_JumpForwards()
    call CompensateForPUM()
    exec g:_uspy "UltiSnips_Manager.jump_forwards()"
    return ""
endfunction

function! UltiSnips_FileTypeChanged()
    exec g:_uspy "UltiSnips_Manager.reset_buffer_filetypes()"
    exec g:_uspy "UltiSnips_Manager.add_buffer_filetypes('" . &ft . "')"
    return ""
endfunction

function! UltiSnips_AddSnippet(trigger, value, descr, options, ...)
    " Takes the same arguments as SnippetManager.add_snippet:
    " (trigger, value, descr, options, ft = "all", globals = None)
    exec g:_uspy "args = vim.eval(\"a:000\")"
    exec g:_uspy "trigger = vim.eval(\"a:trigger\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "descr = vim.eval(\"a:descr\")"
    exec g:_uspy "options = vim.eval(\"a:options\")"
    exec g:_uspy "UltiSnips_Manager.add_snippet(trigger, value, descr, options, *args)"
    return ""
endfunction

function! UltiSnips_Anon(value, ...)
    " Takes the same arguments as SnippetManager.expand_anon:
    " (value, trigger="", descr="", options="", globals = None)
    exec g:_uspy "args = vim.eval(\"a:000\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "UltiSnips_Manager.expand_anon(value, *args)"
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
    exec 'xnoremap ' . g:UltiSnipsExpandTrigger. ' :call UltiSnips_SaveLastVisualSelection()<cr>gvs'
    exec "inoremap <silent> " . g:UltiSnipsJumpBackwardTrigger . " <C-R>=UltiSnips_JumpBackwards()<cr>"
    exec "snoremap <silent> " . g:UltiSnipsJumpBackwardTrigger . " <Esc>:call UltiSnips_JumpBackwards()<cr>"
    exec "inoremap <silent> " . g:UltiSnipsListSnippets . " <C-R>=UltiSnips_ListSnippets()<cr>"
    exec "snoremap <silent> " . g:UltiSnipsListSnippets . " <Esc>:call UltiSnips_ListSnippets()<cr>"

    snoremap <silent> <BS> <c-g>c
    snoremap <silent> <DEL> <c-g>c
    snoremap <silent> <c-h> <c-g>c
endf

function! UltiSnips_CursorMoved()
    exec g:_uspy "UltiSnips_Manager.cursor_moved()"
endf
function! UltiSnips_EnteredInsertMode()
    exec g:_uspy "UltiSnips_Manager.entered_insert_mode()"
endf
function! UltiSnips_LeavingBuffer()
    exec g:_uspy "UltiSnips_Manager.leaving_buffer()"
endf
" }}}
" COMPLETE FUNCTIONS {{{
function! UltiSnipsFiletypeComplete(arglead, cmdline, cursorpos)
    let ret = {}
    let items = map(
    \   split(globpath(&runtimepath, 'syntax/*.vim'), '\n'),
    \   'fnamemodify(v:val, ":t:r")'
    \ )
    call insert(items, 'all')
    for item in items
        if !has_key(ret, item) && item =~ '^'.a:arglead
            let ret[item] = 1
        endif
    endfor

    return sort(keys(ret))
endfunction

" }}}

"" STARTUP CODE {{{

" Expand our path
exec g:_uspy "import vim, os, sys"
exec g:_uspy "new_path = vim.eval('expand(\"<sfile>:h\")')"
exec g:_uspy "vim.command(\"let g:UltiSnipsPythonPath = '%s'\" % new_path)"
exec g:_uspy "sys.path.append(new_path)"
exec g:_uspy "from UltiSnips import UltiSnips_Manager"
exec g:_uspy "UltiSnips_Manager.expand_trigger = vim.eval('g:UltiSnipsExpandTrigger')"
exec g:_uspy "UltiSnips_Manager.forward_trigger = vim.eval('g:UltiSnipsJumpForwardTrigger')"
exec g:_uspy "UltiSnips_Manager.backward_trigger = vim.eval('g:UltiSnipsJumpBackwardTrigger')"

au CursorMovedI * call UltiSnips_CursorMoved()
au CursorMoved * call UltiSnips_CursorMoved()
au BufLeave * call UltiSnips_LeavingBuffer()

call UltiSnips_MapKeys()

let did_UltiSnips_vim=1

" }}}
" vim: ts=8 sts=4 sw=4
