"""Regression tests for issue #751.

A post_jump action that called a typeahead-consuming Vim function (e.g.
input()) used to leak parts of the queued move command (`a`, `v3G10|o3G4|o`,
etc.) into the buffer as literal text because `input()` swallowed the leading
`<Esc>` of the feedkeys()'d move, leaving the rest of the keys to be processed
in the original insert mode.

Maelan's minimal repro:
https://github.com/SirVer/ultisnips/issues/751#issuecomment-421159566
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class PostJumpInput_EmptyTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def test_snippet():
            vim.command('call input("pause")')
        endglobal

        post_jump "if snip.tabstop == 0: test_snippet()"
        snippet post
        [${1}][${0}]
        endsnippet
        """
    }
    # Append "\n" so the input("pause") call inside the post_jump action
    # gets its ENTER and returns; otherwise vim hangs at the prompt.
    keys = "post" + EX + JF + "\n"
    wanted = "[][]"


class PostJumpInput_DefaultedTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def test_snippet():
            vim.command('call input("pause")')
        endglobal

        post_jump "if snip.tabstop == 0: test_snippet()"
        snippet postdef
        [${1}][${0:default}]
        endsnippet
        """
    }
    # Append "\n" so the input("pause") call inside the post_jump action
    # gets its ENTER and returns; otherwise vim hangs at the prompt.
    keys = "postdef" + EX + JF + "\n"
    wanted = "[][default]"
