if exists('did_plugin_ultisnips') || &cp
    finish
endif
let did_plugin_ultisnips=1

" CI tests against Vim 9.1+, but older versions down to 8.2 may still work.
" Neovim reports a low 'version' (801) for Vim compatibility, so skip the
" check there — Neovim compatibility is validated separately in CI.
if !has('nvim') && version < 802
   echohl WarningMsg
   echom  "UltiSnips requires Vim >= 8.2"
   echohl None
   finish
endif

" Show the buffered diagnostic lines as a scratch buffer. Splits at
" VimEnter when the plugin loads during startup (so we don't fight with
" the arglist / quickfix), or immediately if Vim is already up (the
" test-suite reload path).
function! s:UltiSnipsShowDiagBuffer(lines) abort
    let g:UltiSnipsPythonDiagnostics = a:lines
    let s:ultisnips_pending_diag = a:lines
    if v:vim_did_enter
        call s:UltiSnipsOpenDiagBuffer()
    else
        augroup UltiSnipsPythonDiag
            au!
            au VimEnter * ++once call s:UltiSnipsOpenDiagBuffer()
        augroup END
    endif
endfunction

function! s:UltiSnipsOpenDiagBuffer() abort
    if !exists('s:ultisnips_pending_diag')
        return
    endif
    let l:lines = s:ultisnips_pending_diag
    unlet s:ultisnips_pending_diag
    botright new
    silent! exe 'file' fnameescape('[UltiSnips Python diagnostics]')
    setlocal buftype=nofile bufhidden=hide noswapfile nobuflisted
    setlocal filetype=
    call setline(1, l:lines)
    setlocal nomodifiable nomodified
endfunction

" UltiSnips needs Python 3. Bail with a clear message if Vim wasn't
" compiled with python3 support at all, so we don't fall through to the
" runtime-check below (which would just say "Python is broken" without
" distinguishing missing-from-build vs broken-at-load).
if !has('python3')
    if !get(g:, 'UltiSnipsNoPythonWarning', 0)
        let s:diag = [
            \ 'UltiSnips: Python 3 is not available; UltiSnips is disabled.',
            \ '',
            \ 'See :help UltiSnips-requirements for setup instructions.',
            \ '',
            \ ]
        if has('nvim')
            call add(s:diag, 'Neovim diagnostics:')
            if exists('g:python3_host_prog')
                call add(s:diag, '    g:python3_host_prog = ' . g:python3_host_prog)
            else
                call add(s:diag, '    g:python3_host_prog is not set.')
            endif
            call add(s:diag, '')
            call add(s:diag, 'Neovim needs the `pynvim` package in the Python it uses for')
            call add(s:diag, 'the python3 provider. Run `:checkhealth provider.python` to')
            call add(s:diag, 'see which interpreter Neovim picked and what is missing.')
        else
            call add(s:diag, 'Vim must be compiled with the +python3 feature.')
            call add(s:diag, 'Run `vim --version | grep python3` to confirm.')
        endif
        call add(s:diag, '')
        call add(s:diag, 'If you think this is a bug, please file an issue at')
        call add(s:diag, '    https://github.com/SirVer/ultisnips/issues/new')
        call add(s:diag, 'and include everything in this buffer plus the output of')
        if has('nvim')
            call add(s:diag, '    :checkhealth provider.python')
            call add(s:diag, '    nvim --version')
        else
            call add(s:diag, '    vim --version')
        endif
        call add(s:diag, '')
        call add(s:diag, 'Silence this message with `let g:UltiSnipsNoPythonWarning = 1`.')
        call s:UltiSnipsShowDiagBuffer(s:diag)
        unlet s:diag
    endif
    finish
endif

" We are sourcing map_keys.vim here, because we want the UltiSnips trigger
" variables to be defined before trying to load the Python code. However, we
" do not want to map the keys yet - in case something goes wrong with the
" loading, we do not want to have spuriously mapped keys; i.e. a half loaded
" plugin (see #1658, #1679).
runtime autoload/UltiSnips/map_keys.vim

" `has('python3')` is necessary but not sufficient: Vim can be compiled
" with dynamic Python support and still fail to load libpython at
" runtime, or have UltiSnips off the Python path entirely. Force the
" lazy load now by asking Python to flip a Vim-side flag — if either
" libpython or the UltiSnips package import fails, the flag stays zero
" and we bail before registering autocmds that would otherwise re-raise
" E370 / E263 / NameError on every keystroke (#1237, #1209).
"
" When the import fails we let Python populate a list of diagnostic
" lines (traceback + sys.executable / sys.path / sys.version) in
" `g:ultisnips_py3_diag` so a user filing a bug report has the full
" picture — see #1685. The list is consumed and unlet below.
let s:ultisnips_python3_ok = 0
let g:ultisnips_py3_diag = []
try
    py3 << EOF
try:
    import vim
    from UltiSnips import UltiSnips_Manager
    vim.command('let s:ultisnips_python3_ok = 1')
except Exception:
    import sys as _sys
    import traceback as _tb
    _lines = ['Python diagnostics:']
    _lines.append('    sys.version    : ' + _sys.version.replace('\n', ' '))
    _lines.append('    sys.executable : ' + _sys.executable)
    _lines.append('    sys.prefix     : ' + _sys.prefix)
    _lines.append('    sys.path:')
    for _p in _sys.path:
        _lines.append('        ' + _p)
    _lines.append('')
    _lines.append('Traceback:')
    for _l in _tb.format_exc().rstrip('\n').split('\n'):
        _lines.append('    ' + _l)
    vim.vars['ultisnips_py3_diag'] = _lines
EOF
catch
    " Catchable Python load failures (E370, E263) land here; the import
    " block above never ran so the diag list stays empty.
    let g:ultisnips_py3_diag = ['Traceback (from Vim):'] + split(v:exception, "\n")
endtry
if !s:ultisnips_python3_ok
    if !get(g:, 'UltiSnipsNoPythonWarning', 0)
        let s:diag = [
            \ 'UltiSnips: Python 3 is present but unusable; UltiSnips is disabled.',
            \ '',
            \ 'See :help UltiSnips-requirements for setup instructions.',
            \ '',
            \ ]
        call extend(s:diag, g:ultisnips_py3_diag)
        call add(s:diag, '')
        call add(s:diag, 'If you think this is a bug, please file an issue at')
        call add(s:diag, '    https://github.com/SirVer/ultisnips/issues/new')
        call add(s:diag, 'and include everything in this buffer.')
        call add(s:diag, '')
        call add(s:diag, 'Silence this message with `let g:UltiSnipsNoPythonWarning = 1`.')
        call s:UltiSnipsShowDiagBuffer(s:diag)
        unlet s:diag
    endif
    unlet! g:ultisnips_py3_diag
    finish
endif
unlet! g:ultisnips_py3_diag

" The Commands we define.
command! -bang -nargs=? -complete=customlist,UltiSnips#FileTypeComplete UltiSnipsEdit
    \ :call UltiSnips#Edit(<q-bang>, <q-args>)

command! -nargs=1 UltiSnipsAddFiletypes :call UltiSnips#AddFiletypes(<q-args>)
command! -nargs=1 UltiSnipsRemoveFiletypes :call UltiSnips#RemoveFiletypes(<q-args>)

command! UltiSnipsListLocations :call UltiSnips#ListSnippetLocations()

augroup UltiSnips_AutoTrigger
    au!
    au InsertCharPre * call UltiSnips#TrackChange()
    au TextChangedI * call UltiSnips#TrackChange()
    if exists('##TextChangedP')
        au TextChangedP * call UltiSnips#TrackChange()
    endif
augroup END

call UltiSnips#map_keys#MapKeys()

" vim: ts=8 sts=4 sw=4
