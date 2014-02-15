#!/usr/bin/env python
# encoding: utf-8

"""Parses tokens into text objects."""

from UltiSnips.text_objects._lexer import tokenize, EscapeCharToken, \
    VisualToken, TransformationToken, TabStopToken, MirrorToken, \
    PythonCodeToken, VimLCodeToken, ShellCodeToken
from UltiSnips.position import Position
from UltiSnips.text_objects._escaped_char import EscapedChar
from UltiSnips.text_objects._mirror import Mirror
from UltiSnips.text_objects._python_code import PythonCode
from UltiSnips.text_objects._shell_code import ShellCode
from UltiSnips.text_objects._tabstop import TabStop
from UltiSnips.text_objects._transformation import Transformation
from UltiSnips.text_objects._viml_code import VimLCode
from UltiSnips.text_objects._visual import Visual

_TOKEN_TO_TEXTOBJECT = {
    EscapeCharToken: EscapedChar,
    VisualToken: Visual,
    ShellCodeToken: ShellCode,
    PythonCodeToken: PythonCode,
    VimLCodeToken: VimLCode,
}

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

def _do_parse(all_tokens, seen_ts, parent_to, text, indent):
    """Recursive function that actually creates the objects."""
    tokens = list(tokenize(text, indent, parent_to.start))
    for token in tokens:
        all_tokens.append((parent_to, token))
        if isinstance(token, TabStopToken):
            ts = TabStop(parent_to, token)
            seen_ts[token.number] = ts

            _do_parse(all_tokens, seen_ts, ts, token.initial_text, indent)
        else:
            klass = _TOKEN_TO_TEXTOBJECT.get(token.__class__, None)
            if klass is not None:
                klass(parent_to, token)

def parse_text_object(parent_to, text, indent):
    """Parses a text object from 'text' assuming the current 'indent'. Will
    instantiate all the objects and link them as children to parent_to. Will
    also put the initial text into Vim."""
    seen_ts = {}
    all_tokens = []

    _do_parse(all_tokens, seen_ts, parent_to, text, indent)
    _resolve_ambiguity(all_tokens, seen_ts)
    _create_transformations(all_tokens, seen_ts)

    if 0 not in seen_ts:
        mark = all_tokens[-1][1].end # Last token is always EndOfText
        m1 = Position(mark.line, mark.col)
        TabStop(parent_to, 0, mark, m1)
    parent_to.replace_initial_text()
