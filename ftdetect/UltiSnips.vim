" This has to be called before ftplugins are loaded. Therefore 
" it is here in ftdetect though it maybe shouldn't
if has("autocmd")
    autocmd FileType * call UltiSnipsFileTypeChangedWrapper()
endif

function UltiSnipsFileTypeChangedWrapper()
    if exists("*UltiSnips_FileTypeChanged")
        call UltiSnips_FileTypeChanged()
    endif
endfunction


