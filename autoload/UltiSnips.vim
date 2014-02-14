" File: UltiSnips.vim
" Author: Holger Rapp <SirVer@gmx.de>
" Description: The Ultimate Snippets solution for Vim

if exists('did_UltiSnips_autoload') || &cp || version < 700
    finish
endif

" Define dummy version of function called by autocommand setup in
" ftdetect/UltiSnips.vim. If the function isn't defined (probably due to
" using a copy of vim without python support) it will cause an error anytime a
" new file is opened.
function! UltiSnips_FileTypeChanged()
endfunction

" Kludge to make sure that if the python module is loaded first, all of this
" initialization in this file is indeed done.
function! UltiSnips#EnsureAutoloadScriptWasRun()
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

" Should UltiSnips map JumpForwardTrigger and JumpBackwardTrigger only during
" snippet expansion?
if !exists("g:UltiSnipsClearJumpTrigger")
    let g:UltiSnipsClearJumpTrigger = 1
endif
" }}}


" FUNCTIONS {{{
function! s:compensate_for_pum()
    """ The CursorMovedI event is not triggered while the popup-menu is visible,
    """ and it's by this event that UltiSnips updates its vim-state. The fix is
    """ to explicitly check for the presence of the popup menu, and update
    """ the vim-state accordingly.
    if pumvisible()
        exec g:_uspy "UltiSnips_Manager._cursor_moved()"
    endif
endfunction

function! UltiSnips#Edit(...)
    if a:0 == 1 && a:1 != ''
        let type = a:1
    else
        exec g:_uspy "vim.command(\"let type = '%s'\" % UltiSnips_Manager._primary_filetype)"
    endif
    exec g:_uspy "vim.command(\"let file = '%s'\" % UltiSnips_Manager._file_to_edit(vim.eval(\"type\")))"

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

function! UltiSnips#AddFiletypes(filetypes)
    exec g:_uspy "UltiSnips_Manager.add_buffer_filetypes('" . a:filetypes . ".all')"
    return ""
endfunction

function! UltiSnips#FileTypeComplete(arglead, cmdline, cursorpos)
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

function! UltiSnips#MapKeys()
    " Map the keys correctly
    if g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger

        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippetOrJump()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippetOrJump()<cr>"
    else
        exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=UltiSnips#ExpandSnippet()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsExpandTrigger . " <Esc>:call UltiSnips#ExpandSnippet()<cr>"
        if g:UltiSnipsClearJumpTrigger == 0
            exec "inoremap <silent> " . g:UltiSnipsJumpForwardTrigger  . " <C-R>=UltiSnips#JumpForwards()<cr>"
            exec "snoremap <silent> " . g:UltiSnipsJumpForwardTrigger  . " <Esc>:call UltiSnips#JumpForwards()<cr>"
        endif
    endif
    exec 'xnoremap ' . g:UltiSnipsExpandTrigger. ' :call UltiSnips#SaveLastVisualSelection()<cr>gvs'
    if g:UltiSnipsClearJumpTrigger == 0
        exec "inoremap <silent> " . g:UltiSnipsJumpBackwardTrigger . " <C-R>=UltiSnips#JumpBackwards()<cr>"
        exec "snoremap <silent> " . g:UltiSnipsJumpBackwardTrigger . " <Esc>:call UltiSnips#JumpBackwards()<cr>"
    endif
    exec "inoremap <silent> " . g:UltiSnipsListSnippets . " <C-R>=UltiSnips#ListSnippets()<cr>"
    exec "snoremap <silent> " . g:UltiSnipsListSnippets . " <Esc>:call UltiSnips#ListSnippets()<cr>"

    snoremap <silent> <BS> <c-g>c
    snoremap <silent> <DEL> <c-g>c
    snoremap <silent> <c-h> <c-g>c
endf

function! UltiSnips#MapInnerKeys()
    if g:UltiSnipsExpandTrigger != g:UltiSnipsJumpForwardTrigger
        exec "inoremap <buffer> <silent> " . g:UltiSnipsJumpForwardTrigger . " <C-R>=UltiSnips#JumpForwards()<cr>"
        exec "snoremap <buffer> <silent> " . g:UltiSnipsJumpForwardTrigger . " <Esc>:call UltiSnips#JumpForwards()<cr>"
    endif
    exec "inoremap <buffer> <silent> " . g:UltiSnipsJumpBackwardTrigger . " <C-R>=UltiSnips#JumpBackwards()<cr>"
    exec "snoremap <buffer> <silent> " . g:UltiSnipsJumpBackwardTrigger . " <Esc>:call UltiSnips#JumpBackwards()<cr>"
endf

function! UltiSnips#RestoreInnerKeys()
    if g:UltiSnipsExpandTrigger != g:UltiSnipsJumpForwardTrigger
        exec "iunmap <buffer> " . g:UltiSnipsJumpForwardTrigger
        exec "sunmap <buffer> " . g:UltiSnipsJumpForwardTrigger
    endif
    exec "iunmap <buffer> " . g:UltiSnipsJumpBackwardTrigger
    exec "sunmap <buffer> " . g:UltiSnipsJumpBackwardTrigger
endf

function! UltiSnips#ExpandSnippet()
    exec g:_uspy "UltiSnips_Manager.expand()"
    return ""
endfunction

function! UltiSnips#ExpandSnippetOrJump()
    call s:compensate_for_pum()
    exec g:_uspy "UltiSnips_Manager.expand_or_jump()"
    return ""
endfunction

function! UltiSnips#ListSnippets()
    exec g:_uspy "UltiSnips_Manager.list_snippets()"
    return ""
endfunction

function! UltiSnips#SnippetsInCurrentScope()
    let g:current_ulti_dict = {}
    exec g:_uspy "UltiSnips_Manager.snippets_in_current_scope()"
    return g:current_ulti_dict
endfunction

function! UltiSnips#SaveLastVisualSelection()
    exec g:_uspy "UltiSnips_Manager._save_last_visual_selection()"
    return ""
endfunction

function! UltiSnips#JumpBackwards()
    call s:compensate_for_pum()
    exec g:_uspy "UltiSnips_Manager.jump_backwards()"
    return ""
endfunction

function! UltiSnips#JumpForwards()
    call s:compensate_for_pum()
    exec g:_uspy "UltiSnips_Manager.jump_forwards()"
    return ""
endfunction

function! UltiSnips#FileTypeChanged()
    exec g:_uspy "UltiSnips_Manager.reset_buffer_filetypes()"
    exec g:_uspy "UltiSnips_Manager.add_buffer_filetypes('" . &ft . "')"
    return ""
endfunction

function! UltiSnips#AddSnippet(trigger, value, description, options, ...)
    " Takes the same arguments as SnippetManager.add_snippet:
    " (trigger, value, description, options, ft = "all", globals = None)
    exec g:_uspy "args = vim.eval(\"a:000\")"
    exec g:_uspy "trigger = vim.eval(\"a:trigger\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "description = vim.eval(\"a:description\")"
    exec g:_uspy "options = vim.eval(\"a:options\")"
    exec g:_uspy "UltiSnips_Manager.add_snippet(trigger, value, description, options, *args)"
    return ""
endfunction

function! UltiSnips#Anon(value, ...)
    " Takes the same arguments as SnippetManager.expand_anon:
    " (value, trigger="", description="", options="", globals = None)
    exec g:_uspy "args = vim.eval(\"a:000\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "UltiSnips_Manager.expand_anon(value, *args)"
    return ""
endfunction


function! UltiSnips#CursorMoved()
    exec g:_uspy "UltiSnips_Manager._cursor_moved()"
endf

function! UltiSnips#LeavingBuffer()
    exec g:_uspy "UltiSnips_Manager._leaving_buffer()"
endf

function! UltiSnips#LeavingInsertMode()
    exec g:_uspy "UltiSnips_Manager._leaving_insert_mode()"
endfunction
" }}}

" Expand our path
exec g:_uspy "import vim, os, sys"
exec g:_uspy "new_path = os.path.abspath(os.path.join(
    \ vim.eval('expand(\"<sfile>:h\")'), '..', 'pythonx'))"
exec g:_uspy "vim.command(\"let g:UltiSnipsPythonPath = '%s'\" % new_path)"
exec g:_uspy "if not hasattr(vim, 'VIM_SPECIAL_PATH'): sys.path.append(new_path)"
exec g:_uspy "from UltiSnips import UltiSnips_Manager"

let did_UltiSnips_autoload=1
