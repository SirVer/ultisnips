" This has to be called before ftplugins are loaded. Therefore
" it is here in ftdetect though it maybe shouldn't
if has("autocmd")
   augroup UltiSnipsFileType
      au!
      autocmd FileType * if exists('*UltiSnips#FileTypeChanged')|call UltiSnips#FileTypeChanged()|endif
   augroup END
endif
