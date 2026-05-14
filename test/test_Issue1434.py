"""Regression tests for #1434.

Three sub-bugs with `snip.expand_anon` called from snippet actions:

  1. post_expand on an EMPTY outer snippet: anon's first tabstop is
     skipped — Vim lands directly on $2.
  2. post_expand on a NON-EMPTY outer snippet: anon's first tabstop is
     skipped AND the body is split across the outer snippet's text.
  3. post_jump on an EMPTY outer snippet: cursor lands one column to the
     left of where it should after expand_anon.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class Issue1434_PostExpandAnonOnEmptySnippet(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.expand_anon('1:$1;2:$2;')"
        snippet aa "description"
        endsnippet
        """
    }
    # Trigger the empty snippet; the post_expand should drop in
    # `1:$1;2:$2;` and select $1 first. Typing `A` lands in $1.
    keys = "aa" + EX + "A" + JF + "B"
    wanted = "1:A;2:B;"


class Issue1434_PostExpandAnonOnNonEmptySnippet(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.expand_anon('1:$1;2:$2;')"
        snippet aa "description"
        XXYY
        endsnippet
        """
    }
    keys = "aa" + EX + "A" + JF + "B"
    # The anon snippet should land *after* XXYY (or wherever the outer
    # snippet's cursor parked), not split through the middle of it.
    wanted = "XXYY1:A;2:B;"


class Issue1434_PostJumpAnonOnEmptySnippet(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_jump "snip.expand_anon('1:$1;2:$2;')"
        snippet aa "description"
        endsnippet
        """
    }
    # Empty outer snippet: pressing Tab fires post_jump → expand_anon.
    # The anon should put us at $1 and typing `A` should land between
    # `1:` and `;` cleanly.
    keys = "aa" + EX + "A" + JF + "B"
    wanted = "1:A;2:B;"
