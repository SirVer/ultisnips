function! PyVimSnips_ExpandSnippet()
    py << EOF
from PySnipEmu import PySnipSnippets
PySnipSnippets.try_expand()
EOF

    return ""
endfunction

function! PyVimSnips_JumpBackwards()
    py << EOF
from PySnipEmu import PySnipSnippets
PySnipSnippets.try_expand(True)
EOF
    return ""
endfunction


" Expand our path
python from PySnipEmu import PySnipSnippets

inoremap <Tab> <C-R>=PyVimSnips_ExpandSnippet()<cr>
snoremap <Tab> <Esc>:call PyVimSnips_ExpandSnippet()<cr>
inoremap + <C-R>=PyVimSnips_JumpBackwards()<cr>
snoremap + <Esc>:call PyVimSnips_JumpBackwards()<cr>

au CursorMovedI * py PySnipSnippets.cursor_moved()
au InsertEnter * py PySnipSnippets.entered_insert_mode()
   
