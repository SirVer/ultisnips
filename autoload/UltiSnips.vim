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
