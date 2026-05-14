"""Regression test for #1013.

`snip.cursor.set(...)` in a post_jump action is honoured when the target
tabstop is empty, but is dropped when the target has default text — the
select-mode coordinates are captured *before* the action runs and the
action's cursor move is discarded.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class Issue1013_PostJumpCursorMoveHonouredWhenTargetHasDefault(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def shift_cursor():
            snip.buffer[snip.cursor[0]] = "prepended" + snip.buffer[snip.cursor[0]]
            snip.cursor.set(snip.cursor[0], snip.cursor[1] + 9)
        endglobal

        post_jump "if snip.tabstop == 0: shift_cursor()"
        snippet testdef
        [${1}][${0:default}]
        endsnippet
        """
    }
    # Triggering and jumping to $0 should leave the placeholder "default"
    # selected; the post_jump prepends 9 chars and adjusts the cursor by
    # +9, so the select-mode range needs to shift accordingly.
    keys = "testdef" + EX + JF + "REPLACED"
    wanted = "prepended[][REPLACED]"


class Issue1013_PostJumpCursorMoveOnEmptyTargetStillWorks(_VimTest):
    """Control case — cursor.set on an empty $0 should keep working."""

    files = {
        "us/all.snippets": r"""
        global !p
        def shift_cursor():
            snip.buffer[snip.cursor[0]] = "prepended" + snip.buffer[snip.cursor[0]]
            snip.cursor.set(snip.cursor[0], snip.cursor[1] + 9)
        endglobal

        post_jump "if snip.tabstop == 0: shift_cursor()"
        snippet testnodef
        [${1}][${0}]
        endsnippet
        """
    }
    keys = "testnodef" + EX + JF
    wanted = "prepended[][]"
