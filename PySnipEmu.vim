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

python PySnipSnippets.add_snippet("hello", "Hallo Welt!\nUnd Wie gehts?")
python PySnipSnippets.add_snippet("echo","$0 run")


python PySnipSnippets.add_snippet("if", "if(${1:/* condition */})\n{\n${0:/* code */}\n}")




