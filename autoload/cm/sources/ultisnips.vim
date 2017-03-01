
func! cm#sources#ultisnips#cm_refresh(opt,ctx)

	if get(s:, 'disable', 0)
		return
	endif

	" UltiSnips#SnippetsInCurrentScope
	" {
	"     "modeline": "Vim modeline",
	"     "au": "augroup ... autocmd block",
	"     ......
	" }
	let l:snips = UltiSnips#SnippetsInCurrentScope()

	let l:matches = []

	" The available snippet list is fairly small, simply dump the whole list
	" here, leave the filtering work to NCM's standard filter.  This would
	" reduce the work done by vimscript.
	let l:matches = map(keys(l:snips),'{"word":v:val,"dup":1,"icase":1,"info": l:snips[v:val]}')

	call cm#complete(a:opt, a:ctx, a:ctx['startcol'], l:matches)

endfunc


"
" Tips: Add this to your vimrc for triggering snips popup with <c-u>
"
" let g:UltiSnipsExpandTrigger = "<Plug>(ultisnips_expand)"
" inoremap <silent> <c-u> <c-r>=cm#sources#ultisnips#trigger_or_popup("\<Plug>(ultisnips_expand)")<cr>
"
func! cm#sources#ultisnips#trigger_or_popup(trigger_key)

	let l:ctx = cm#context()

	let l:typed = l:ctx['typed']
	let l:kw = matchstr(l:typed,'\v\S+$')
	if len(l:kw)
		call feedkeys(a:trigger_key)
		return ''
	endif

	let l:snips = UltiSnips#SnippetsInCurrentScope()
	let l:matches = map(keys(l:snips),'{"word":v:val,"dup":1,"icase":1,"info": l:snips[v:val]}')
	let l:startcol = l:ctx['col']

	" notify the completion framework
	call cm#complete('cm-ultisnips', l:ctx, l:startcol, l:matches)

	return ''

endfunc

