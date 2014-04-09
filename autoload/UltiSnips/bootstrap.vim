let s:SourcedFile=expand("<sfile>")

function! UltiSnips#bootstrap#Bootstrap()
   if exists('s:did_UltiSnips_bootstrap')
      return
   endif
   let s:did_UltiSnips_bootstrap=1

   if !exists("g:UltiSnipsUsePythonVersion")
       let g:_uspy=":py3 "
       if !has("python3")
           if !has("python")
               if !exists("g:UltiSnipsNoPythonWarning")
                   echo  "UltiSnips requires py >= 2.6 or any py3"
               endif
               unlet g:_uspy
               return
           endif
           let g:_uspy=":py "
       endif
       let g:UltiSnipsUsePythonVersion = "<tab>"
   else
       if g:UltiSnipsUsePythonVersion == 2
           let g:_uspy=":py "
       else
           let g:_uspy=":py3 "
       endif
   endif

   " Expand our path
   exec g:_uspy "import vim, os, sys"
   exec g:_uspy "sourced_file = vim.eval('s:SourcedFile')"
   exec g:_uspy "while not os.path.exists(os.path.join(sourced_file, 'pythonx')):
      \ sourced_file = os.path.dirname(sourced_file)"
   exec g:_uspy "module_path = os.path.join(sourced_file, 'pythonx')"
   exec g:_uspy "vim.command(\"let g:UltiSnipsPythonPath = '%s'\" % module_path)"
   exec g:_uspy "if not hasattr(vim, 'VIM_SPECIAL_PATH'): sys.path.append(module_path)"
   exec g:_uspy "from UltiSnips import UltiSnips_Manager"
endfunction

" The trigger used to expand a snippet.
" NOTE: expansion and forward jumping can, but needn't be the same trigger
if !exists("g:UltiSnipsExpandTrigger")
    let g:UltiSnipsExpandTrigger = "<tab>"
endif

" The trigger used to display all triggers that could possible
" match in the current position.
if !exists("g:UltiSnipsListSnippets")
    let g:UltiSnipsListSnippets = "<c-tab>"
endif

" The trigger used to jump forward to the next placeholder.
" NOTE: expansion and forward jumping can, but needn't be the same trigger
if !exists("g:UltiSnipsJumpForwardTrigger")
    let g:UltiSnipsJumpForwardTrigger = "<c-j>"
endif

" The trigger to jump backward inside a snippet
if !exists("g:UltiSnipsJumpBackwardTrigger")
    let g:UltiSnipsJumpBackwardTrigger = "<c-k>"
endif

" Should UltiSnips unmap select mode mappings automagically?
if !exists("g:UltiSnipsRemoveSelectModeMappings")
    let g:UltiSnipsRemoveSelectModeMappings = 1
end

" If UltiSnips should remove Mappings, which should be ignored
if !exists("g:UltiSnipsMappingsToIgnore")
    let g:UltiSnipsMappingsToIgnore = []
endif

" UltiSnipsEdit will use this variable to decide if a new window
" is opened when editing. default is "normal", allowed are also
" "vertical", "horizontal"
if !exists("g:UltiSnipsEditSplit")
    let g:UltiSnipsEditSplit = 'normal'
endif

" A list of directory names that are searched for snippets.
if !exists("g:UltiSnipsSnippetDirectories")
    let g:UltiSnipsSnippetDirectories = [ "UltiSnips" ]
endif
