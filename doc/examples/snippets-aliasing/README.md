# Aliases for snippets

![gif](https://raw.githubusercontent.com/SirVer/ultisnips/master/doc/examples/snippets-aliasing/demo.gif)

Let's imagine we're editing shell file and we need to debug some vars.

Essentially, we will end up with snippet like that, that will automatically
insert location of the debug statement and variable name.

Example of that snippet is shown below:

```
snippet pr "print debug" bw
`!p
prefix = t[1] + ": %q\\n' "
prefix = "{}:{}: {}".format(
    os.path.basename(px.buffer.get().name),
    str(px.cursor.get()[0]),
    prefix
)
`printf 'XXXXXX `!p snip.rv=prefix`$1 >&2
endsnippet
```

Now, we want to use same debug snippet, but dump variable to the file.
How can we do it?

Simple, declare new snippet in that way:

```
post_jump "px.snippets.expand(snip)"
snippet pd "Description" b
pr$1 >${2:/tmp/debug}
endsnippet
```

This snippet will expand `pr` snippet automatically (note `pr$1` part) after
jumping to the first placeholder (jump will be done automatically by UltiSnips
engine).

`px.snippets.expand(snip)` is declared in that way:

```python
def expand(snip, jump_pos=1):
    if snip.tabstop != jump_pos:
        return

    vim.eval('feedkeys("\<C-R>=UltiSnips#ExpandSnippet()\<CR>")')
```

`px.buffer.get()` and `px.cursor.get()` are simple helpers for the
`vim.current.window.buffer` and `vim.current.window.cursor`.
