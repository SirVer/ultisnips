"""Regression test for #1243.

Reporter had a `2*2matrix` snippet whose `pre_expand` calls
`snip.expand_anon` to generate a `\\begin{pmatrix}` body of the requested
shape. At top level that worked, but typing the trigger inside another
snippet's tabstop (e.g. inside the `equation` snippet's `$1`) returned
out-of-order tabstops in the matrix.

The simplified shape: an outer snippet with `$1/$0` and an inner snippet
whose `pre_expand` builds a body with several tabstops via `expand_anon`.
After expanding the outer and triggering the inner inside `$1`, jumping
forward should walk through the inner's tabstops in order before
returning to the outer's `$0`.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class Issue1243_NestedAnonExpandsTabstopsInOrder(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet outer "outer" bA
        OS
        $1
        OE
        $0
        endsnippet

        pre_expand "snip.buffer[snip.line] = ''; snip.expand_anon('M\n\t$1 & $2\n\t$3 & $4\nE$0')"
        snippet mtx "mtx" wA
        endsnippet
        """
    }
    keys = "outer" + EX + "mtx" + "1" + JF + "2" + JF + "3" + JF + "4" + JF + JF + "END"
    wanted = "OS\nM\n\t1 & 2\n\t3 & 4\nE\nOE\nEND"
