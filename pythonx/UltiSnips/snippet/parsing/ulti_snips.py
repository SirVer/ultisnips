#!/usr/bin/env python3

"""Parses a UltiSnips snippet definition and launches it into Vim."""

from UltiSnips.error import PebkacError
from UltiSnips.snippet.parsing.base import (
    finalize,
    resolve_ambiguity,
    tokenize_snippet_text,
)
from UltiSnips.snippet.parsing.lexer import (
    ChoicesToken,
    EscapeCharToken,
    MirrorToken,
    PythonCodeToken,
    ShellCodeToken,
    TabStopToken,
    TransformationToken,
    VimLCodeToken,
    VisualToken,
)
from UltiSnips.text_objects import (
    Choices,
    EscapedChar,
    PythonCode,
    ShellCode,
    Transformation,
    VimLCode,
    Visual,
)

_TOKEN_TO_TEXTOBJECT = {
    EscapeCharToken: EscapedChar,
    VisualToken: Visual,
    ShellCodeToken: ShellCode,
    PythonCodeToken: PythonCode,
    VimLCodeToken: VimLCode,
    ChoicesToken: Choices,
}

__ALLOWED_TOKENS = [
    EscapeCharToken,
    VisualToken,
    TransformationToken,
    ChoicesToken,
    TabStopToken,
    MirrorToken,
    PythonCodeToken,
    VimLCodeToken,
    ShellCodeToken,
]


def _create_transformations(all_tokens, seen_ts):
    """Create the objects that need to know about tabstops."""
    for parent, token in all_tokens:
        if isinstance(token, TransformationToken):
            if token.number not in seen_ts:
                raise PebkacError(
                    f"Tabstop {token.number} is not known"
                    " but is used by a Transformation"
                )
            Transformation(parent, seen_ts[token.number], token)


def parse_and_instantiate(parent_to, text, indent):
    """Parses a snippet definition in UltiSnips format from 'text' assuming the
    current 'indent'.

    Will instantiate all the objects and link them as children to
    parent_to. Will also put the initial text into Vim.

    """
    all_tokens, seen_ts = tokenize_snippet_text(
        parent_to,
        text,
        indent,
        __ALLOWED_TOKENS,
        __ALLOWED_TOKENS,
        _TOKEN_TO_TEXTOBJECT,
    )
    resolve_ambiguity(all_tokens, seen_ts)
    _create_transformations(all_tokens, seen_ts)
    finalize(all_tokens, seen_ts, parent_to)
