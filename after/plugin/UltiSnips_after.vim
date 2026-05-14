" Called after everything else to reclaim keys (Needed for Supertab)

" Bail out if plugin/UltiSnips.vim itself bailed (Python missing or libpython
" load failure). The :UltiSnipsEdit command is registered only after the
" Python check passes, so its absence is a load-failure signal — don't
" reinstall the key mappings on top of a half-loaded plugin (#1658, #1679).
if !exists(':UltiSnipsEdit')
    finish
endif

if exists("b:did_after_plugin_ultisnips_after")
   finish
endif
let b:did_after_plugin_ultisnips_after = 1

call UltiSnips#map_keys#MapKeys()
