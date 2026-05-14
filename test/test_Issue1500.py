"""Tests for #1500.

`UltiSnipsJumped` is a `User` autocommand that fires every time the
cursor lands on a tabstop. It is the global hook that lets external
plugins (completion engines in particular) react to the snippet
engine moving the cursor, without having to add a `post_jump` action
to every snippet.

The final `$0` tabstop is excluded because the snippet is being torn
down right after - the right hook for that case is
`UltiSnipsExitLastSnippet`, which already exists.
"""

from test.vim_test_case import VimTestCase as _VimTest

_AUTOCMD_SETUP = (
    "let g:_1500_count = 0",
    "augroup Issue1500",
    "  autocmd!",
    "  autocmd User UltiSnipsJumped let g:_1500_count += 1",
    "augroup END",
)


class Issue1500_FiresOnInitialExpansion(_VimTest):
    """Even the very first jump that lands the cursor on `$1` after
    expansion goes through `_jump`, so `UltiSnipsJumped` fires once.
    We verify by surfacing `g:_1500_count` into the buffer at the end."""

    snippets = ("trg", "$1$0")
    text_before = ""
    text_after = ""
    # trg<Tab> expands; X fills $1; <C-O>:let @c=...<CR> stores the count
    # in the named register; <C-R>c pastes it.
    keys = "trg\tX\x0f:let @c = 'count=' . g:_1500_count\r\x12c"
    wanted = "Xcount=1"

    def _extra_vim_config(self, vim_config):
        vim_config.extend(_AUTOCMD_SETUP)


class Issue1500_FiresOnEverySubsequentJump(_VimTest):
    """Each `JumpForwards` step fires the event again so a completion
    engine can pop up its menu at every tabstop."""

    snippets = ("trg", "$1 then $2 then $3")
    text_before = ""
    text_after = ""
    keys = "trg\tA?B?C\x0f:let @c = 'count=' . g:_1500_count\r\x12c"
    wanted = "A then B then Ccount=3"

    def _extra_vim_config(self, vim_config):
        vim_config.extend(_AUTOCMD_SETUP)


class Issue1500_DoesNotFireForFinalTabStop(_VimTest):
    """A snippet body that ends in an implicit `$0` should NOT trigger
    `UltiSnipsJumped` when the user runs out of stops - the snippet
    is being torn down, and `UltiSnipsExitLastSnippet` is the
    appropriate event for that case."""

    snippets = ("trg", "$1 done")
    text_before = ""
    text_after = ""
    # Initial expansion lands on $1 (counts 1). Then `?` (JF) jumps to
    # $0 -- that jump should NOT increment the counter.
    keys = "trg\tX?\x0f:let @c = 'count=' . g:_1500_count\r\x12c"
    wanted = "X donecount=1"

    def _extra_vim_config(self, vim_config):
        vim_config.extend(_AUTOCMD_SETUP)
