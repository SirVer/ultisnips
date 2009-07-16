
"" FUNCTIONS

function! UltiSnips_ExpandSnippet()
    if exists('g:SuperTabMappingForward')
        if g:SuperTabMappingForward == "<s-tab>"
            let SuperTabKey = "\<c-n>"
        elseif g:SuperTabMappingBackward == "<s-tab>"
            let SuperTabKey = "\<c-p>"
        endif
    endif
   
    " Now, really expand something
    py << EOF
if not UltiSnips_Manager.try_expand():
   vim.command("""if exists('SuperTabKey')
   call feedkeys(SuperTabKey)
endif
""")
EOF
   
   return ""
endfunction

function! UltiSnips_JumpBackwards()
    py << EOF
UltiSnips_Manager.jump(True)
EOF
    return ""
endfunction

function! UltiSnips_JumpForwards()
    py << EOF
UltiSnips_Manager.jump()
EOF
    return ""
endfunction


"" STARTUP CODE

" Expand our path
python << EOF
import vim, os, sys

for p in vim.eval("&runtimepath").split(','):
   dname = p + os.path.sep + "plugin"
   if os.path.exists(dname + os.path.sep + "UltiSnips"):
      if dname not in sys.path:
         sys.path.append(dname)
      break

from UltiSnips import UltiSnips_Manager
EOF

" You can remap these
inoremap <Tab> <C-R>=UltiSnips_ExpandSnippet()<cr>
snoremap <Tab> <Esc>:call UltiSnips_ExpandSnippet()<cr>
inoremap <C-k> <C-R>=UltiSnips_JumpBackwards()<cr>
snoremap <C-k> <Esc>:call UltiSnips_JumpBackwards()<cr>
inoremap <C-j> <C-R>=UltiSnips_JumpForwards()<cr>
snoremap <C-j> <Esc>:call UltiSnips_JumpForwards()<cr>

" Do not remap this.
snoremap <BS> <Esc>:py  UltiSnips_Manager.backspace_while_selected()<cr>

au CursorMovedI * py UltiSnips_Manager.cursor_moved()
au InsertEnter * py UltiSnips_Manager.entered_insert_mode()
   
