"""Tests for the 'p' snippet option (GH #1207).

A snippet declared with the 'p' option expands when the user has typed
any non-empty prefix of the trigger. Only the characters the user actually
typed are removed before the expansion is inserted.
"""

from test.constant import EX
from test.vim_test_case import VimTestCase as _VimTest


class PartialPrefix_ExpandsOnSingleChar(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet import "imp" p
        IMPORT_BODY
        endsnippet
        """
    }
    keys = "i" + EX
    wanted = "IMPORT_BODY"


class PartialPrefix_ExpandsOnIntermediatePrefix(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet import "imp" p
        IMPORT_BODY
        endsnippet
        """
    }
    keys = "imp" + EX
    wanted = "IMPORT_BODY"


class PartialPrefix_ExpandsOnFullTrigger(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet import "imp" p
        IMPORT_BODY
        endsnippet
        """
    }
    keys = "import" + EX
    wanted = "IMPORT_BODY"


class PartialPrefix_PreservesTextBeforeTypedPrefix(_VimTest):
    """Only the typed prefix is consumed - text before it stays put."""

    files = {
        "us/all.snippets": r"""
        snippet import "imp" p
        IMPORT_BODY
        endsnippet
        """
    }
    keys = "hello imp" + EX
    wanted = "hello IMPORT_BODY"


class PartialPrefix_DoesNotMatchOnEmpty(_VimTest):
    """Without typing anything (just <Tab>), the trigger shouldn't expand."""

    files = {
        "us/all.snippets": r"""
        snippet import "imp" p
        IMPORT_BODY
        endsnippet
        """
    }
    keys = EX
    wanted = EX


class PartialPrefix_WithoutOption_StillRequiresFullTrigger(_VimTest):
    """A plain snippet (no 'p') still requires the full trigger."""

    files = {
        "us/all.snippets": r"""
        snippet import "imp"
        IMPORT_BODY
        endsnippet
        """
    }
    keys = "imp" + EX
    wanted = "imp" + EX
