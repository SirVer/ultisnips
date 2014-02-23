#!/usr/bin/env python
# encoding: utf-8

"""Parses a UltiSnips snippet definition and launches it into Vim."""

from UltiSnips.snippet.parsing._base import tokenize_snippet_text, finalize
from UltiSnips.snippet.parsing._lexer import EscapeCharToken, \
    VisualToken, TransformationToken, TabStopToken, MirrorToken, \
    PythonCodeToken, VimLCodeToken, ShellCodeToken
from UltiSnips.text_objects import EscapedChar, Mirror, PythonCode, \
        ShellCode, TabStop, Transformation, VimLCode, Visual

_TOKEN_TO_TEXTOBJECT = {
    EscapeCharToken: EscapedChar,
    VisualToken: Visual,
    ShellCodeToken: ShellCode,
    PythonCodeToken: PythonCode,
    VimLCodeToken: VimLCode,
}

__ALLOWED_TOKENS = [
    EscapeCharToken, VisualToken, TransformationToken, TabStopToken,
    MirrorToken, PythonCodeToken, VimLCodeToken, ShellCodeToken
]

def _resolve_ambiguity(all_tokens, seen_ts):
    """$1 could be a Mirror or a TabStop. This figures this out."""
    for parent, token in all_tokens:
        if isinstance(token, MirrorToken):
            if token.number not in seen_ts:
                seen_ts[token.number] = TabStop(parent, token)
            else:
                Mirror(parent, seen_ts[token.number], token)

def _create_transformations(all_tokens, seen_ts):
    """Create the objects that need to know about tabstops."""
    for parent, token in all_tokens:
        if isinstance(token, TransformationToken):
            if token.number not in seen_ts:
                raise RuntimeError(
                    "Tabstop %i is not known but is used by a Transformation"
                    % token.number)
            Transformation(parent, seen_ts[token.number], token)


def parse_and_instantiate(parent_to, text, indent):
    """Parses a snippet definition in UltiSnips format from 'text' assuming the
    current 'indent'. Will instantiate all the objects and link them as
    children to parent_to. Will also put the initial text into Vim."""
    all_tokens, seen_ts = tokenize_snippet_text(parent_to, text, indent,
            __ALLOWED_TOKENS, __ALLOWED_TOKENS, _TOKEN_TO_TEXTOBJECT)
    _resolve_ambiguity(all_tokens, seen_ts)
    _create_transformations(all_tokens, seen_ts)
    finalize(all_tokens, seen_ts, parent_to)
