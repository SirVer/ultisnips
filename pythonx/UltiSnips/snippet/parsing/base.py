#!/usr/bin/env python
# encoding: utf-8

"""Common functionality of the snippet parsing codes."""

from UltiSnips.position import Position
from UltiSnips.snippet.parsing.lexer import tokenize, TabStopToken
from UltiSnips.text_objects import TabStop

from UltiSnips.text_objects import Mirror
from UltiSnips.snippet.parsing.lexer import MirrorToken


def resolve_ambiguity(all_tokens, seen_ts):
    """$1 could be a Mirror or a TabStop.

    This figures this out.

    """
    for parent, token in all_tokens:
        if isinstance(token, MirrorToken):
            if token.number not in seen_ts:
                seen_ts[token.number] = TabStop(parent, token)
            else:
                Mirror(parent, seen_ts[token.number], token)


def tokenize_snippet_text(
    snippet_instance,
    text,
    indent,
    allowed_tokens_in_text,
    allowed_tokens_in_tabstops,
    token_to_textobject,
):
    """Turns 'text' into a stream of tokens and creates the text objects from
    those tokens that are mentioned in 'token_to_textobject' assuming the
    current 'indent'.

    The 'allowed_tokens_in_text' define which tokens will be recognized
    in 'text' while 'allowed_tokens_in_tabstops' are the tokens that
    will be recognized in TabStop placeholder text.

    """
    seen_ts = {}
    all_tokens = []

    def _do_parse(parent, text, allowed_tokens):
        """Recursive function that actually creates the objects."""
        tokens = list(tokenize(text, indent, parent.start, allowed_tokens))
        for token in tokens:
            all_tokens.append((parent, token))
            if isinstance(token, TabStopToken):
                ts = TabStop(parent, token)
                seen_ts[token.number] = ts
                _do_parse(ts, token.initial_text, allowed_tokens_in_tabstops)
            else:
                klass = token_to_textobject.get(token.__class__, None)
                if klass is not None:
                    text_object = klass(parent, token)

                    # TabStop has some subclasses (e.g. Choices)
                    if isinstance(text_object, TabStop):
                        seen_ts[text_object.number] = text_object

    _do_parse(snippet_instance, text, allowed_tokens_in_text)
    return all_tokens, seen_ts


def finalize(all_tokens, seen_ts, snippet_instance):
    """Adds a tabstop 0 if non is in 'seen_ts' and brings the text of the
    snippet instance into Vim."""
    if 0 not in seen_ts:
        mark = all_tokens[-1][1].end  # Last token is always EndOfText
        m1 = Position(mark.line, mark.col)
        TabStop(snippet_instance, 0, mark, m1)
