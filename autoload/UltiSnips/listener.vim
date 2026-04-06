" Vim buffer change listener glue for UltiSnips.
" Uses listener_add() (Vim 8.1.1420+) to get reliable, mode-independent
" buffer change notifications.

let s:listener_id = -1
let g:_ultisnips_listener_changes = []
let g:_ultisnips_listener_suppressed = 0

function! s:on_change(bufnr, start, end, added, changes) abort
    if g:_ultisnips_listener_suppressed
        return
    endif
    for change in a:changes
        call add(g:_ultisnips_listener_changes, {
            \ 'lnum': change.lnum,
            \ 'end': change.end,
            \ 'added': change.added,
            \ })
    endfor
endfunction

function! UltiSnips#listener#Attach(bufnr) abort
    call UltiSnips#listener#Detach()
    let s:listener_id = listener_add(function('s:on_change'), a:bufnr)
endfunction

function! UltiSnips#listener#Detach() abort
    if s:listener_id != -1
        call listener_remove(s:listener_id)
        let s:listener_id = -1
    endif
    let g:_ultisnips_listener_changes = []
endfunction

function! UltiSnips#listener#Flush() abort
    if s:listener_id != -1
        call listener_flush()
    endif
endfunction
