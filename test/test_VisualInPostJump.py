"""Tests for `snip.visual_text` / `snip.visual_mode` in `post_jump` (GH #1524).

Both attributes are now exposed alongside `snip.tabstop` / `snip.tabstops`
so authors can build snippets that consume the visual selection without
having to stash it in `context` first.
"""

from test.constant import ESC, EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class VisualInPostJump_ExposesText(_VimTest):
    """`snip.visual_text` carries the selection through to `post_jump`."""

    files = {
        "us/all.snippets": r"""
        global !p
        def append_visual(snip):
            if snip.tabstop == 0:
                line = snip.snippet_end[0] + 1
                snip.buffer[line:line] = ['VT:' + snip.visual_text]
        endglobal

        post_jump "append_visual(snip)"
        snippet vp "post-jump visual" b
        BODY $1
        endsnippet
        """
    }
    # Type "hello", visually select it, expand the snippet, then jump to
    # $0 so `post_jump` can read `snip.visual_text`.
    keys = "hello" + ESC + "0vllll" + EX + "vp" + EX + "X" + JF
    wanted = "BODY X\nVT:hello"


class VisualInPostJump_EmptyWithoutSelection(_VimTest):
    """`snip.visual_text` is the empty string when no visual selection
    preceded the expansion - the action must not raise AttributeError."""

    files = {
        "us/all.snippets": r"""
        global !p
        def record(snip):
            if snip.tabstop == 0:
                line = snip.snippet_end[0] + 1
                snip.buffer[line:line] = ['VT:[' + snip.visual_text + ']']
        endglobal

        post_jump "record(snip)"
        snippet vp2 "post-jump no visual"
        BODY$1
        endsnippet
        """
    }
    keys = "vp2" + EX + "X" + JF
    wanted = "BODYX\nVT:[]"
