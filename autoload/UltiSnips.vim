if exists("b:did_autoload_ultisnips")
    finish
endif
let b:did_autoload_ultisnips = 1

" Also import vim as we expect it to be imported in many places.
py3 import vim
py3 from UltiSnips import UltiSnips_Manager

function! s:compensate_for_pum() abort
    """ The CursorMovedI event is not triggered while the popup-menu is visible,
    """ and it's by this event that UltiSnips updates its vim-state. The fix is
    """ to explicitly check for the presence of the popup menu, and update
    """ the vim-state accordingly.
    if pumvisible()
        py3 UltiSnips_Manager._cursor_moved()
    endif
endfunction

function! s:is_floating(winId) abort
    if has('nvim')
        return get(nvim_win_get_config(a:winId), 'relative', '') !=# ''
    endif

    return 0
endfunction

function! UltiSnips#Edit(bang, ...) abort
    if a:0 == 1 && a:1 != ''
        let type = a:1
    else
        let type = ""
    endif
    py3 vim.command("let file = '%s'" % UltiSnips_Manager._file_to_edit(vim.eval("type"), vim.eval('a:bang')))

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
    py3 UltiSnips_Manager.add_buffer_filetypes(vim.eval("a:filetypes"))
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
    py3 UltiSnips_Manager.expand()
    return ""
endfunction

function! UltiSnips#ExpandSnippetOrJump() abort
    call s:compensate_for_pum()
    py3 UltiSnips_Manager.expand_or_jump()
    return ""
endfunction

function! UltiSnips#ListSnippets() abort
    py3 UltiSnips_Manager.list_snippets()
    return ""
endfunction

function! UltiSnips#SnippetsInCurrentScope(...) abort
    let g:current_ulti_dict = {}
    let all = get(a:, 1, 0)
    if all
      let g:current_ulti_dict_info = {}
    endif
    py3 UltiSnips_Manager.snippets_in_current_scope(int(vim.eval("all")))
    return g:current_ulti_dict
endfunction

function! UltiSnips#CanExpandSnippet() abort
	py3 vim.command("let can_expand = %d" % UltiSnips_Manager.can_expand())
	return can_expand
endfunction

function! UltiSnips#CanJumpForwards() abort
	py3 vim.command("let can_jump_forwards = %d" % UltiSnips_Manager.can_jump_forwards())
	return can_jump_forwards
endfunction

function! UltiSnips#CanJumpBackwards() abort
	py3 vim.command("let can_jump_backwards = %d" % UltiSnips_Manager.can_jump_backwards())
	return can_jump_backwards
endfunction

function! UltiSnips#SaveLastVisualSelection() range abort
    py3 UltiSnips_Manager._save_last_visual_selection()
    return ""
endfunction

function! UltiSnips#JumpBackwards() abort
    call s:compensate_for_pum()
    py3 UltiSnips_Manager.jump_backwards()
    return ""
endfunction

function! UltiSnips#JumpForwards() abort
    call s:compensate_for_pum()
    py3 UltiSnips_Manager.jump_forwards()
    return ""
endfunction

function! UltiSnips#AddSnippetWithPriority(trigger, value, description, options, filetype, priority) abort
    py3 trigger = vim.eval("a:trigger")
    py3 value = vim.eval("a:value")
    py3 description = vim.eval("a:description")
    py3 options = vim.eval("a:options")
    py3 filetype = vim.eval("a:filetype")
    py3 priority = vim.eval("a:priority")
    py3 UltiSnips_Manager.add_snippet(trigger, value, description, options, filetype, priority)
    return ""
endfunction

function! UltiSnips#Anon(value, ...) abort
    " Takes the same arguments as SnippetManager.expand_anon:
    " (value, trigger="", description="", options="")
    py3 args = vim.eval("a:000")
    py3 value = vim.eval("a:value")
    py3 UltiSnips_Manager.expand_anon(value, *args)
    return ""
endfunction

function! UltiSnips#CursorMoved() abort
    py3 UltiSnips_Manager._cursor_moved()
endf

function! UltiSnips#LeavingBuffer() abort
    let from_preview = getwinvar(winnr('#'), '&previewwindow')
    let to_preview = getwinvar(winnr(), '&previewwindow')
    let from_floating = s:is_floating(win_getid('#'))
    let to_floating = s:is_floating(win_getid())

    if !(from_preview || to_preview || from_floating || to_floating)
        py3 UltiSnips_Manager._leaving_buffer()
    endif
endf

function! UltiSnips#LeavingInsertMode() abort
    py3 UltiSnips_Manager._leaving_insert_mode()
endfunction

function! UltiSnips#TrackChange() abort
    py3 UltiSnips_Manager._track_change()
endfunction

function! UltiSnips#RefreshSnippets() abort
    py3 UltiSnips_Manager._refresh_snippets()
endfunction
" }}}
