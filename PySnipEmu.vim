pyfile PySnipEmu.py


function! PyVimSnips_ExpandSnippet()
    py << EOF
from PySnipEmu import PySnipSnippets
PySnipSnippets.try_expand()
EOF

    return ""
endfunction


function! PyVimSnips_SelectWord(len)
    return "\<esc>".'v'.a:len."l\<c-g>"
endf

" Run the unit test suite that comes 
" with the application
function! PyVimSnips_RunTests()
    pyfile test.py
endfunction

python from PySnipEmu import PySnipSnippets

inoremap <Tab> <C-R>=PyVimSnips_ExpandSnippet()<cr>
snoremap <Tab> <Esc>:call PyVimSnips_ExpandSnippet()<cr>

au CursorMovedI * py PySnipSnippets.cursor_moved()
au InsertEnter * py PySnipSnippets.entered_insert_mode()
 

