if exists('did_plugin_ultisnips') || &cp
    finish
endif
let did_plugin_ultisnips=1

" CI tests against Vim 9.1+, but older versions down to 8.2 may still work.
" Neovim reports a low 'version' (801) for Vim compatibility, so skip the
" check there — Neovim compatibility is validated separately in CI.
if !has('nvim') && version < 820
   echohl WarningMsg
   echom  "UltiSnips requires Vim >= 8.2"
   echohl None
   finish
endif

" Bail out cleanly when Python 3 is unusable, instead of letting every
" autocmd and mapping below re-raise E370/E263 (Vim can't load libpython)
" or `NameError: UltiSnips_Manager` (the package isn't on the Python path)
" on every keystroke (#1237, #1209).
"
" `has('python3')` is necessary but not sufficient: Vim can be compiled
" with dynamic Python support and still fail to load the library at
" runtime. We force the lazy load now by asking Python to flip a
" Vim-side flag — if either the libpython load or the UltiSnips package
" import fails, the flag stays zero.
"
" The documented `g:UltiSnipsNoPythonWarning` opt-out
" (see |UltiSnips-python-warning|) silences the message itself.
let s:ultisnips_python3_ok = 0
let s:ultisnips_python3_error = ''
if has('python3')
    try
        py3 << EOF
try:
    import vim
    from UltiSnips import UltiSnips_Manager  # noqa: F401
    vim.command('let s:ultisnips_python3_ok = 1')
except Exception as _err:
    import traceback as _tb
    _msg = _tb.format_exception_only(type(_err), _err)[-1].strip()
    vim.command("let s:ultisnips_python3_error = " + repr(_msg))
EOF
    catch
        " Catchable Python load failures (E370, E263) end up here, in which
        " case `s:ultisnips_python3_error` was never set — fall through to
        " the generic message below.
    endtry
endif
if !s:ultisnips_python3_ok
    if !get(g:, 'UltiSnipsNoPythonWarning', 0)
        echohl WarningMsg
        echom 'UltiSnips: Python 3 is not usable in this Vim; disabling UltiSnips.'
        if !empty(s:ultisnips_python3_error)
            echom '           ' . s:ultisnips_python3_error
        endif
        echom '           See :help UltiSnips-requirements for setup.'
        echom '           Silence this message with `let g:UltiSnipsNoPythonWarning = 1`.'
        echohl None
    endif
    finish
endif

" Enable Post debug server config
if !exists("g:UltiSnipsDebugServerEnable")
   let g:UltiSnipsDebugServerEnable = 0
endif

if !exists("g:UltiSnipsDebugHost")
   let g:UltiSnipsDebugHost = 'localhost'
endif

if !exists("g:UltiSnipsDebugPort")
   let g:UltiSnipsDebugPort = 8080
endif

if !exists("g:UltiSnipsPMDebugBlocking")
   let g:UltiSnipsPMDebugBlocking = 0
endif


" The Commands we define.
command! -bang -nargs=? -complete=customlist,UltiSnips#FileTypeComplete UltiSnipsEdit
    \ :call UltiSnips#Edit(<q-bang>, <q-args>)

command! -nargs=1 UltiSnipsAddFiletypes :call UltiSnips#AddFiletypes(<q-args>)

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
