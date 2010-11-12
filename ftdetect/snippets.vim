" recognize .snippet files
if has("autocmd")
    autocmd BufNewFile,BufRead *.snippets setf snippet
endif
