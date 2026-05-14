"""Regression test for #1427.

After an undo unwinds the buffer state created by an expansion, the
snippet must be considered finished. Reporter's repro at the time was
that `_active_snippets` still held the (now stale) snippet, so the next
`<Tab>` ran the post_jump action — and the `snip.expand_anon('aaa')`
inside it dropped the literal `aaa` into a buffer that, to the user,
had no snippet in it.

The fix in #1648 ("Drop snippet on re-entering insert mode outside its
bounds") closes this hole: the `i` after the `dd` re-enters insert mode
on a different line than the snippet was tracking, the snippet is dropped,
and the subsequent `<Tab>` is a plain tab.
"""

from test.constant import ESC, EX
from test.vim_test_case import VimTestCase as _VimTest


class Issue1427_TabAfterUndoIsLiteralTab(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_jump "snip.expand_anon('aaa')"
        snippet sn "description"
        A $1 B
        endsnippet
        """
    }
    # sn<TAB>             expand
    # <Esc>               leave insert; cursor leaves snippet bounds
    # u                   undo unwinds the buffer state
    # i                   re-enter insert mode on a now-empty line; the
    #                     snippet must be dropped here
    # <TAB>               tab must be a literal tab, NOT a jump that
    #                     fires the post_jump action and drops `aaa`.
    keys = "sn" + EX + ESC + "u" + "o" + EX
    wanted = "sn\n\t"
