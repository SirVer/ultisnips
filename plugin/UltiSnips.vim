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

" UltiSnips needs Python 3. Bail with a clear message if Vim wasn't
" compiled with python3 support at all, so we don't fall through to the
" runtime-check below (which would just say "Python is broken" without
" distinguishing missing-from-build vs broken-at-load).
if !has('python3') && !get(g:, 'UltiSnipsNoPythonWarning', 0)
    echohl WarningMsg
    echom 'UltiSnips requires Vim compiled with +python3 support; disabling UltiSnips.'
    echom '          See :help UltiSnips-requirements for setup.'
    echom '          Silence this message with `let g:UltiSnipsNoPythonWarning = 1`.'
    echohl None
endif
if !has('python3')
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
let s:ultisnips_python3_ok = 0
let s:ultisnips_python3_error = ''
try
    py3 << EOF
try:
    import vim
    from UltiSnips import UltiSnips_Manager
    vim.command('let s:ultisnips_python3_ok = 1')
except Exception as _err:
    import traceback as _tb
    _msg = _tb.format_exception_only(type(_err), _err)[-1].strip()
    vim.command("let s:ultisnips_python3_error = " + repr(_msg))
EOF
catch
    " Catchable Python load failures (E370, E263) land here; the import
    " block above never ran so s:ultisnips_python3_error stays empty.
    let s:ultisnips_python3_error = v:exception
endtry
if !s:ultisnips_python3_ok
    if !get(g:, 'UltiSnipsNoPythonWarning', 0)
        echohl WarningMsg
        echom 'UltiSnips: Python 3 is present but unusable; disabling UltiSnips.'
        if !empty(s:ultisnips_python3_error)
            echom '           ' . s:ultisnips_python3_error
        endif
        echom '           See :help UltiSnips-requirements for setup.'
        echom '           Silence this message with `let g:UltiSnipsNoPythonWarning = 1`.'
        echohl None
    endif
    finish
endif

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
