if exists('did_UltiSnips_snipmate_compatibility')
       finish
endif
let did_UltiSnips_snipmate_compatibility = 1

if ! exists('g:snips_author')
       let g:snips_author = "John Doe"
endif

" Filename function, taken from snipMate.vim
fun! Filename(...)
    let filename = expand('%:t:r')
    if filename == '' | return a:0 == 2 ? a:2 : '' | endif
    return !a:0 || a:1 == '' ? filename : substitute(a:1, '$1', filename, 'g')
endf
