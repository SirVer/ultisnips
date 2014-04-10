" File: UltiSnips.vim
" Author: Holger Rapp <SirVer@gmx.de>
" Description: The Ultimate Snippets solution for Vim

if exists('did_UltiSnips_autoload') || &cp || version < 700
    finish
endif
let did_UltiSnips_autoload=1

" Define dummy version of function called by autocommand setup in
" ftdetect/UltiSnips.vim and plugin/UltiSnips.vim.
" If the function isn't defined (probably due to using a copy of vim
" without python support) it would cause an error.
function! UltiSnips#FileTypeChanged()
endfunction
function! UltiSnips#CursorMoved()
endfunction
function! UltiSnips#CursorMoved()
endfunction
function! UltiSnips#LeavingBuffer()
endfunction
function! UltiSnips#LeavingInsertMode()
endfunction

call UltiSnips#bootstrap#Bootstrap()
if !exists("g:_uspy")
   " Delete the autocommands defined in plugin/UltiSnips.vim and
   " ftdetect/UltiSnips.vim.
   augroup UltiSnips
       au!
   augroup END
   augroup UltiSnipsFileType
       au!
   augroup END
   finish
end

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

function! UltiSnips#Edit(bang, ...)
    if a:0 == 1 && a:1 != ''
        let type = a:1
    else
        let type = ""
    endif
    exec g:_uspy "vim.command(\"let file = '%s'\" % UltiSnips_Manager._file_to_edit(vim.eval(\"type\"), vim.eval('a:bang')))"

    if !len(file)
       return
    endif

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
    " Takes the same arguments as SnippetManager.add_snippet.
    echoerr "Deprecated UltiSnips#AddSnippet called. Please use UltiSnips#AddSnippetWithPriority." | sleep 1
    exec g:_uspy "args = vim.eval(\"a:000\")"
    exec g:_uspy "trigger = vim.eval(\"a:trigger\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "description = vim.eval(\"a:description\")"
    exec g:_uspy "options = vim.eval(\"a:options\")"
    exec g:_uspy "UltiSnips_Manager.add_snippet(trigger, value, description, options, *args)"
    return ""
endfunction

function! UltiSnips#AddSnippetWithPriority(trigger, value, description, options, filetype, priority)
    exec g:_uspy "trigger = vim.eval(\"a:trigger\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "description = vim.eval(\"a:description\")"
    exec g:_uspy "options = vim.eval(\"a:options\")"
    exec g:_uspy "filetype = vim.eval(\"a:filetype\")"
    exec g:_uspy "priority = vim.eval(\"a:priority\")"
    exec g:_uspy "UltiSnips_Manager.add_snippet(trigger, value, description, options, filetype, priority)"
    return ""
endfunction

function! UltiSnips#Anon(value, ...)
    " Takes the same arguments as SnippetManager.expand_anon:
    " (value, trigger="", description="", options="")
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
