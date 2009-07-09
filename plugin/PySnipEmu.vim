
"" FUNCTIONS

function! PyVimSnips_ExpandSnippet()
    if exists('g:SuperTabMappingForward')
        if g:SuperTabMappingForward == "<s-tab>"
            let SuperTabKey = "\<c-n>"
        elseif g:SuperTabMappingBackward == "<s-tab>"
            let SuperTabKey = "\<c-p>"
        endif
    endif
    
    if pumvisible() " Update snippet if completion is used, or deal with supertab
        if exists('SuperTabKey')
            call feedkeys(SuperTabKey) | return ''
        endif
        call feedkeys("\<esc>a", 'n') " Close completion menu
        call feedkeys("\<tab>") | return ''
    endif

   " Now, really expand something
    py << EOF
if not PySnipSnippets.try_expand():
   vim.command("""if exists('SuperTabKey')
   call feedkeys(SuperTabKey)
endif
""")
EOF
   
   return ""
endfunction

function! PyVimSnips_JumpBackwards()
    py << EOF
PySnipSnippets.jump(True)
EOF
    return ""
endfunction

function! PyVimSnips_JumpForwards()
    py << EOF
PySnipSnippets.jump()
EOF
    return ""
endfunction


"" STARTUP CODE

" Expand our path
python << EOF
import vim, os, sys

for p in vim.eval("&runtimepath").split(','):
   dname = p + os.path.sep + "plugin"
   if os.path.exists(dname + os.path.sep + "PySnipEmu"):
      if dname not in sys.path:
         sys.path.append(dname)
      break

from PySnipEmu import PySnipSnippets
EOF

" You can remap these
inoremap <Tab> <C-R>=PyVimSnips_ExpandSnippet()<cr>
snoremap <Tab> <Esc>:call PyVimSnips_ExpandSnippet()<cr>
inoremap <C-k> <C-R>=PyVimSnips_JumpBackwards()<cr>
snoremap <C-k> <Esc>:call PyVimSnips_JumpBackwards()<cr>
inoremap <C-j> <C-R>=PyVimSnips_JumpForwards()<cr>
snoremap <C-j> <Esc>:call PyVimSnips_JumpForwards()<cr>

" Do not remap this.
snoremap <BS> <Esc>:py  PySnipSnippets.backspace_while_selected()<cr>

au CursorMovedI * py PySnipSnippets.cursor_moved()
au InsertEnter * py PySnipSnippets.entered_insert_mode()
   
