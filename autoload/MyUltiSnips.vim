let g:UltiSnipsSnippetsDir = expand("~/.ultisnips")

if !isdirectory(UltiSnipsSnippetsDir)
	exec "!git clone https://github.com/countoren/ultisnips-snippets.git ".expand(UltiSnipsSnippetsDir)
endif

