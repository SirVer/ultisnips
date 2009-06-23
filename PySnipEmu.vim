pyfile PySnipEmu.py


function! PyVimSnips_ExpandSnippet()
    py << EOF
from PySnipEmu import PySnipSnippets
PySnipSnippets.try_expand()
EOF

    return ""
endfunction

" Run the unit test suite that comes 
" with the application
function! PyVimSnips_RunTests()
    pyfile test.py
endfunction

python from PySnipEmu import PySnipSnippets

inoremap <Tab> <C-R>=PyVimSnips_ExpandSnippet()<cr>

python PySnipSnippets.add_snippet("hello", "Hello World!")
python PySnipSnippets.add_snippet("echo", "$0 run")





