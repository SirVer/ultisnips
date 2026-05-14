"""Tests for the `post_finish` snippet action (GH #1415).

A `post_finish` action runs once when the snippet is removed from the
active stack - whether the user jumped through the final tabstop, moved
the cursor out of the snippet, or left the buffer.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class PostFinish_RunsOnFinalTabstop(_VimTest):
    """The post_finish action should run when the user jumps through the
    final tabstop. We verify by writing a marker line to a known position
    immediately after the snippet body."""

    files = {
        "us/all.snippets": r"""
        global !p
        def record(snip):
            line = snip.snippet_end[0] + 1
            snip.buffer[line:line] = ['FINISHED']
        endglobal

        post_finish "record(snip)"
        snippet pf "post-finish single tabstop"
        body${1:placeholder}tail$0
        endsnippet
        """
    }
    keys = "pf" + EX + JF
    wanted = "bodyplaceholdertail\nFINISHED"


class PostFinish_RunsOnce(_VimTest):
    """The post_finish action should run exactly once per snippet
    expansion - even if the user jumps back and forth between tabstops."""

    files = {
        "us/all.snippets": r"""
        global !p
        def record(snip):
            line = snip.snippet_end[0] + 1
            existing = snip.buffer[line] if line < len(snip.buffer) else ''
            snip.buffer[line:line] = [existing + 'X']
        endglobal

        post_finish "record(snip)"
        snippet pf2 "post-finish runs once"
        ${1:a}.${2:b}.$0
        endsnippet
        """
    }
    # Jump through two named tabstops to reach $0; bouncing in between
    # would call post_jump (not post_finish).
    keys = "pf2" + EX + "1" + JF + "2" + JF
    wanted = "1.2.\nX"
