"""Tests for the 'x' snippet option (GH #1399).

A snippet declared with the 'x' option lands in normal mode once the user
has jumped through to the final tabstop ($0).
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class FinishInNormalMode_LandsInNormalAtFinalTabstop(_VimTest):
    """Inserting in normal mode via `i` should be needed to add more text -
    if we were still in insert mode the `i` would just be typed."""

    files = {
        "us/all.snippets": r"""
        snippet bb "exit" x
        foo${1:bar}baz$0
        endsnippet
        """
    }
    # bb<Tab> expands. We're on tabstop 1 (in select mode over "bar").
    # JF (?) advances to $0 -- option 'x' should put us in normal mode.
    # Typing `iX` in normal mode runs `i` (enter insert mode) then types X.
    keys = "bb" + EX + JF + "iX"
    wanted = "foobarbaXz"


class FinishInNormalMode_NoOption_LandsInInsertMode(_VimTest):
    """Same snippet without 'x' parks the cursor in insert mode -- the `i`
    is typed verbatim."""

    files = {
        "us/all.snippets": r"""
        snippet bb "no exit"
        foo${1:bar}baz$0
        endsnippet
        """
    }
    keys = "bb" + EX + JF + "iX"
    wanted = "foobarbaziX"


class FinishInNormalMode_EmptyTabstopOrigin(_VimTest):
    """Regression for the issue reporter: jumping from an *empty* tabstop
    ($1 with no default placeholder, so we entered insert mode rather
    than select mode) must still land in normal mode at $0.

    Probe Vim's `mode()` right after the jump and stash it in the buffer.
    The `:stopinsert` queued inside `vim_helper.select()` is not reliably
    consumed before the next user keystroke; this test pins the synchronous
    Esc-via-feedkeys behaviour that fixes it.
    """

    files = {
        "us/all.snippets": r"""
        snippet footle "Description" x
        ${1} $1: foo$0
        endsnippet
        """
    }
    keys = "footle" + EX + "X" + JF + ":put =mode(1)\n"
    wanted = "X X: foo\nn"
