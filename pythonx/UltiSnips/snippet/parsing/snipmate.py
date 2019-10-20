#!/usr/bin/env python
# encoding: utf-8

"""Parses a snipMate snippet definition and launches it into Vim."""

from UltiSnips.snippet.parsing.base import (
    tokenize_snippet_text,
    finalize,
    resolve_ambiguity,
)
from UltiSnips.snippet.parsing.lexer import (
    EscapeCharToken,
    VisualToken,
    TabStopToken,
    MirrorToken,
    ShellCodeToken,
)
from UltiSnips.text_objects import EscapedChar, Mirror, VimLCode, Visual

_TOKEN_TO_TEXTOBJECT = {
    EscapeCharToken: EscapedChar,
    VisualToken: Visual,
    ShellCodeToken: VimLCode,  # `` is VimL in snipMate
}

__ALLOWED_TOKENS = [
    EscapeCharToken,
    VisualToken,
    TabStopToken,
    MirrorToken,
    ShellCodeToken,
]

__ALLOWED_TOKENS_IN_TABSTOPS = [
    EscapeCharToken,
    VisualToken,
    MirrorToken,
    ShellCodeToken,
]


def parse_and_instantiate(parent_to, text, indent):
    """Parses a snippet definition in snipMate format from 'text' assuming the
    current 'indent'.

    Will instantiate all the objects and link them as children to
    parent_to. Will also put the initial text into Vim.

    """
    all_tokens, seen_ts = tokenize_snippet_text(
        parent_to,
        text,
        indent,
        __ALLOWED_TOKENS,
        __ALLOWED_TOKENS_IN_TABSTOPS,
        _TOKEN_TO_TEXTOBJECT,
    )
    resolve_ambiguity(all_tokens, seen_ts)
    finalize(all_tokens, seen_ts, parent_to)
