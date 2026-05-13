"""Reproducers for #903 — auto-pair quote with iA snippet.

Snippet:
    snippet ' "auto pair" iA
        '${1:${VISUAL}}'$0
    endsnippet

Reporter wants:
    '       -> '|'         (cursor between)
    '<Tab>' -> ''|          (jump past second ', then type another ')

But because the snippet is `iA` on trigger `'`, every `'` keystroke that
lands at a word boundary re-triggers the snippet, so typing `'` after
jumping out re-expands and the result is `''<cursor>'`.
"""

from test.constant import JF
from test.vim_test_case import VimTestCase as _VimTest


class Issue903_FirstQuoteExpands(_VimTest):
    files = {
        "us/all.snippets": "\n".join(
            [
                'snippet \' "auto pair" iA',
                "'${1:${VISUAL}}'$0",
                "endsnippet",
            ]
        )
    }
    keys = "'"
    wanted = "''"


class Issue903_TabJumpsOutOfPair(_VimTest):
    files = {
        "us/all.snippets": "\n".join(
            [
                'snippet \' "auto pair" iA',
                "'${1:${VISUAL}}'$0",
                "endsnippet",
            ]
        )
    }
    # Type `'` to expand; jump to $0; expand-or-jump should land at $0.
    keys = "'" + JF
    wanted = "''"


# Demonstrates the reporter's gripe: a second `'` after jumping re-triggers
# the iA snippet. This is unavoidable for a single-char iA trigger.
class Issue903_SecondQuoteRetriggers(_VimTest):
    files = {
        "us/all.snippets": "\n".join(
            [
                'snippet \' "auto pair" iA',
                "'${1:${VISUAL}}'$0",
                "endsnippet",
            ]
        )
    }
    keys = "'" + JF + "'"
    # The 2nd `'` lands at the $0 position (end of snippet). iA fires
    # on the new `'`, producing another pair.
    wanted = "''''"
