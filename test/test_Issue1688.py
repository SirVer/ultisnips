"""Regression tests for #1688.

`post_expand` action's `snip.expand_anon` silently drops the expansion
when the anon body has no `$N` (only `$0`, or plain text).

Sibling of #1434 (`test_Issue1434.py`), which only covered bodies that
contain a `$1` tabstop.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class Issue1688_PostExpandAnonPlainText(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.expand_anon('plain text result')"
        snippet noTab "no tabstop"
        endsnippet
        """
    }
    keys = "noTab" + EX
    wanted = "plain text result"


class Issue1688_PostExpandAnonOnlyZeroTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        post_expand "snip.expand_anon('result-with-$0-tabstop')"
        snippet justZero "with just \$0"
        endsnippet
        """
    }
    keys = "justZero" + EX + "MID"
    wanted = "result-with-MID-tabstop"


class Issue1688_PostExpandAnonWithFirstTabstop(_VimTest):
    """Sanity check: ${1:...} already worked before — keep it passing."""

    files = {
        "us/all.snippets": r"""
        post_expand "snip.expand_anon('${1:result}')"
        snippet withTab "with \$1 tabstop"
        endsnippet
        """
    }
    keys = "withTab" + EX + JF + "after"
    wanted = "resultafter"
