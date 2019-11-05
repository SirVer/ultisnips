" Called after everything else to reclaim keys (Needed for Supertab)

if exists("b:did_after_plugin_ultisnips_after")
   finish
endif
let b:did_after_plugin_ultisnips_after = 1

call UltiSnips#map_keys#MapKeys()
