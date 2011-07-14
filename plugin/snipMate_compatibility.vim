" File: snipMate_compatibility.vim
" Author: Phillip Berndt <phillip.berndt@gmail.com>
" Description: Snipmate compatibility helper functions for UltiSnips
"
" Snipmate defines a function named Filename and a variable called
" g:snips_author for use in snippet subtitutions. See
"  https://github.com/msanders/snipmate.vim/blob/master/doc/snipMate.txt
" for details.
"

if exists('did_UltiSnips_snipmate_compatibility')
	finish
endif
let did_UltiSnips_snipmate_compatibility = 1

" Define g:snips_author; some snipmate snippets use this
if ! exists('g:snips_author')
	let g:snips_author = "John Doe"
endif

" Filename function, taken from snipMate.vim {{{
fun! Filename(...)
    let filename = expand('%:t:r')
    if filename == '' | return a:0 == 2 ? a:2 : '' | endif
    return !a:0 || a:1 == '' ? filename : substitute(a:1, '$1', filename, 'g')
endf
" }}}

