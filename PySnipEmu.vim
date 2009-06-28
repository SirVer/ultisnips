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

python PySnipSnippets.add_snippet("echo","echo ${1:Hallo}")
python PySnipSnippets.add_snippet("hello", "Hallo Welt!\nUnd Wie gehts?")
python PySnipSnippets.add_snippet("hallo", "hallo ${0:End} ${1:Beginning}")


python << EOF
PySnipSnippets.add_snippet("if",
"""if(${1:/* condition */}) {
   ${2:/* code */}
}
""")
EOF

au CursorMovedI * py PySnipSnippets.cursor_moved()
au InsertEnter * py PySnipSnippets.entered_insert_mode()
 

