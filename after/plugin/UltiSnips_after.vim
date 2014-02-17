" File: UltiSnips_after.vim
" Author: Holger Rapp <SirVer@gmx.de>
" Description: Called after everything else to reclaim keys (Needed for
"              Supertab)
" Last Modified: July 27, 2009

if exists('did_UltiSnips_after') || &cp || version < 700
	finish
endif

call UltiSnips#map_keys#MapKeys()

let did_UltiSnips_after=1
