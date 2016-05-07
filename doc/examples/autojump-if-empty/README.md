# Autojump from tabstop when it's empty

UltiSnips offers enough API to support automatic jump from one tabstop to
another when some condition is encountered.

One example of applying that behaviour is jump on the next placeholder when
current becomes empty when user types `<BS>` or another erase sequence when
tabstop is active.

Let's imagine, that we have following snippet:

![snippet](https://raw.githubusercontent.com/SirVer/ultisnips/master/doc/examples/autojump-if-empty/snippet.gif)

First placeholder, surrounded by braces, can be erased by user, but then 
surrounding quotes will left untouched, and user should remove quotes and
one space, and only then jump to next placeholder, that equals to **5** total
keypresses: <kbd>BackSpace</kbd> (erase placeholder), <kbd>BackSpace</kbd> and
<kbd>Delete</kbd> (erase braces), <kbd>Delete</kbd> (erase space),
<kbd>Ctrl+J</kbd> (jump to next placeholder).

However, with UltiSnips, it can be done via only one keypress:
<kbd>BackSpace</kbd>:

![demo](https://raw.githubusercontent.com/SirVer/ultisnips/master/doc/examples/autojump-if-empty/demo.gif)

## Implementation

Using awesome [vim-pythonx
library](https://github.com/reconquest/vim-pythonx/blob/master/pythonx/px/snippets.py),
which provides set of functions to make coding little bit easier.

```
global !p
import px.snippets
endglobal

global !p
# This function will jump to next placeholder when first is empty.
def jump_to_second_when_first_is_empty(snip):
    if px.snippets.get_jumper_position(snip) == 1:
        if not px.snippets.get_jumper_text(snip):
            px.snippets.advance_jumper(snip)

# This function will clean up first placeholder when this is empty.
def clean_first_placeholder(snip):
    # Jumper is a helper for performing jumps in UltiSnips.
    px.snippets.make_jumper(snip)

    if snip.tabstop == 2:
        line = snip.buffer[snip.cursor[0]]
        snip.buffer[snip.cursor[0]] = \
            line[:snip.tabstops[1].start[1]-2] + \
            line[snip.tabstops[1].end[1]+1:]
        snip.cursor.set(
            snip.cursor[0],
            snip.cursor[1] - 3,
        )
endglobal

context "px.snippets.make_context(snip)"
post_jump "clean_first_placeholder(snip)"
snippet x "Description" b
`!p jump_to_second_when_first_is_empty(snip)
`func (${1:blah}) $2() {
    $3
}
endsnippet
```
