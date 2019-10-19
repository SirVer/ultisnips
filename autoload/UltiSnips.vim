if exists("b:did_autoload_ultisnips") || !exists("g:_uspy")
    finish
endif
let b:did_autoload_ultisnips = 1

" Also import vim as we expect it to be imported in many places.
exec g:_uspy "import vim"
exec g:_uspy "from UltiSnips import UltiSnips_Manager"

function! s:compensate_for_pum() abort
    """ The CursorMovedI event is not triggered while the popup-menu is visible,
    """ and it's by this event that UltiSnips updates its vim-state. The fix is
    """ to explicitly check for the presence of the popup menu, and update
    """ the vim-state accordingly.
    if pumvisible()
        exec g:_uspy "UltiSnips_Manager._cursor_moved()"
    endif
endfunction

function! UltiSnips#Edit(bang, ...) abort
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
        elseif g:UltiSnipsEditSplit == 'tabdo'
            let mode = 'tabedit'
        elseif g:UltiSnipsEditSplit == 'context'
            let mode = 'vs'
            if winwidth(0) <= 2 * (&tw ? &tw : 80)
                let mode = 'sp'
            endif
        endif
    endif
    exe ':'.mode.' '.escape(file, ' ')
endfunction

function! UltiSnips#AddFiletypes(filetypes) abort
    exec g:_uspy "UltiSnips_Manager.add_buffer_filetypes('" . a:filetypes . "')"
    return ""
endfunction

function! UltiSnips#FileTypeComplete(arglead, cmdline, cursorpos) abort
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

function! UltiSnips#ExpandSnippet() abort
    exec g:_uspy "UltiSnips_Manager.expand()"
    return ""
endfunction

function! UltiSnips#ExpandSnippetOrJump() abort
    call s:compensate_for_pum()
    exec g:_uspy "UltiSnips_Manager.expand_or_jump()"
    return ""
endfunction

function! UltiSnips#ListSnippets() abort
    exec g:_uspy "UltiSnips_Manager.list_snippets()"
    return ""
endfunction

function! UltiSnips#SnippetsInCurrentScope(...) abort
    let g:current_ulti_dict = {}
    let all = get(a:, 1, 0)
    if all
      let g:current_ulti_dict_info = {}
    endif
    exec g:_uspy "UltiSnips_Manager.snippets_in_current_scope(" . all . ")"
    return g:current_ulti_dict
endfunction

function! UltiSnips#SaveLastVisualSelection() range abort
    exec g:_uspy "UltiSnips_Manager._save_last_visual_selection()"
    return ""
endfunction

function! UltiSnips#JumpBackwards() abort
    call s:compensate_for_pum()
    exec g:_uspy "UltiSnips_Manager.jump_backwards()"
    return ""
endfunction

function! UltiSnips#JumpForwards() abort
    call s:compensate_for_pum()
    exec g:_uspy "UltiSnips_Manager.jump_forwards()"
    return ""
endfunction

function! UltiSnips#AddSnippetWithPriority(trigger, value, description, options, filetype, priority) abort
    exec g:_uspy "trigger = vim.eval(\"a:trigger\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "description = vim.eval(\"a:description\")"
    exec g:_uspy "options = vim.eval(\"a:options\")"
    exec g:_uspy "filetype = vim.eval(\"a:filetype\")"
    exec g:_uspy "priority = vim.eval(\"a:priority\")"
    exec g:_uspy "UltiSnips_Manager.add_snippet(trigger, value, description, options, filetype, priority)"
    return ""
endfunction

function! UltiSnips#Anon(value, ...) abort
    " Takes the same arguments as SnippetManager.expand_anon:
    " (value, trigger="", description="", options="")
    exec g:_uspy "args = vim.eval(\"a:000\")"
    exec g:_uspy "value = vim.eval(\"a:value\")"
    exec g:_uspy "UltiSnips_Manager.expand_anon(value, *args)"
    return ""
endfunction

function! UltiSnips#CursorMoved() abort
    exec g:_uspy "UltiSnips_Manager._cursor_moved()"
endf

function! UltiSnips#LeavingBuffer() abort
    let from_preview = getwinvar(winnr('#'), '&previewwindow')
    let to_preview = getwinvar(winnr(), '&previewwindow')

    if !(from_preview || to_preview)
        exec g:_uspy "UltiSnips_Manager._leaving_buffer()"
    endif
endf

function! UltiSnips#LeavingInsertMode() abort
    exec g:_uspy "UltiSnips_Manager._leaving_insert_mode()"
endfunction

function! UltiSnips#TrackChange() abort
    exec g:_uspy "UltiSnips_Manager._track_change()"
endfunction

function! UltiSnips#RefreshSnippets() abort
    exec g:_uspy "UltiSnips_Manager._refresh_snippets()"
endfunction
" }}}
