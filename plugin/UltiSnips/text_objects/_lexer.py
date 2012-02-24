#!/usr/bin/env python
# encoding: utf-8

"""
Not really a Lexer in the classical sense, but code to hack Snippet Definitions
into Logical Units called Tokens.
"""

import string
import re

from UltiSnips.geometry import Position
from UltiSnips.compatibility import as_unicode

__all__ = [
    "tokenize", "EscapeCharToken", "VisualToken", "TransformationToken", "TabStopToken",
    "MirrorToken", "PythonCodeToken", "VimLCodeToken", "ShellCodeToken"
]

# Helper Classes  {{{
class _TextIterator(object):
    def __init__(self, text, offset):
        self._text = as_unicode(text)
        self._line = offset.line
        self._col = offset.col

        self._idx = 0

    def __iter__(self):
        return self

    def next(self):
        if self._idx >= len(self._text):
            raise StopIteration

        rv = self._text[self._idx]
        if self._text[self._idx] in ('\n', '\r\n'):
            self._line += 1
            self._col = 0
        else:
            self._col += 1
        self._idx += 1

        return rv

    def peek(self, count = 1):
        if count > 1: # This might return '' if nothing is found
            return self._text[self._idx:self._idx + count]
        try:
            return self._text[self._idx]
        except IndexError:
            return None

    @property
    def pos(self):
        return Position(self._line, self._col)

def unescape(s):
    rv = ""
    i = 0
    while i < len(s):
        if i+1 < len(s) and s[i] == '\\':
            rv += s[i+1]
            i += 1
        else:
            rv += s[i]
        i += 1
    return rv

# End: Helper Classes  }}}
# Helper functions  {{{
def _parse_number(stream):
    """
    Expects the stream to contain a number next, returns the number
    without consuming any more bytes
    """
    rv = ""
    while stream.peek() and stream.peek() in string.digits:
        rv += stream.next()

    return int(rv)

def _parse_till_closing_brace(stream):
    """
    Returns all chars till a non-escaped } is found. Other
    non escaped { are taken into account and skipped over.

    Will also consume the closing }, but not return it
    """
    rv = ""
    in_braces = 1
    while True:
        if EscapeCharToken.starts_here(stream, '{}'):
            rv += stream.next() + stream.next()
        else:
            c = stream.next()
            if c == '{': in_braces += 1
            elif c == '}': in_braces -= 1
            if in_braces == 0: break
            rv += c
    return rv

def _parse_till_unescaped_char(stream, chars):
    """
    Returns all chars till a non-escaped char is found.

    Will also consume the closing char, but and return it as second
    return value
    """
    rv = ""
    while True:
        escaped = False
        for c in chars:
            if EscapeCharToken.starts_here(stream, c):
                rv += stream.next() + stream.next()
                escaped = True
        if not escaped:
            c = stream.next()
            if c in chars: break
            rv += c
    return rv, c
# End: Helper functions  }}}

# Tokens  {{{
class Token(object):
    def __init__(self, gen, indent):
        self.initial_text = as_unicode("")
        self.start = gen.pos
        self._parse(gen, indent)
        self.end = gen.pos

class TabStopToken(Token):
    CHECK = re.compile(r'^\${\d+[:}]')

    @classmethod
    def starts_here(klass, stream):
        return klass.CHECK.match(stream.peek(10)) is not None

    def _parse(self, stream, indent):
        stream.next() # $
        stream.next() # {

        self.no = _parse_number(stream)

        if stream.peek() == ":":
            stream.next()
        self.initial_text = _parse_till_closing_brace(stream)

    def __repr__(self):
        return "TabStopToken(%r,%r,%r,%r)" % (
            self.start, self.end, self.no, self.initial_text
        )

class VisualToken(Token):
    CHECK = re.compile(r"^\${VISUAL[:}/]")

    @classmethod
    def starts_here(klass, stream):
        return klass.CHECK.match(stream.peek(10)) is not None

    def _parse(self, stream, indent):
        for i in range(8): # ${VISUAL
            stream.next()

        if stream.peek() == ":":
            stream.next()
        self.alternative_text, c = _parse_till_unescaped_char(stream, '/}')
        self.alternative_text = unescape(self.alternative_text)

        if c == '/': # Transformation going on
            try:
                self.search = _parse_till_unescaped_char(stream, '/')[0]
                self.replace = _parse_till_unescaped_char(stream, '/')[0]
                self.options = _parse_till_closing_brace(stream)
            except StopIteration:
                raise RuntimeError("Invalid ${VISUAL} transformation! Forgot to escape a '/'?")
        else:
            self.search = None
            self.replace = None
            self.options = None

    def __repr__(self):
        return "VisualToken(%r,%r)" % (
            self.start, self.end
        )

class TransformationToken(Token):
    CHECK = re.compile(r'^\${\d+\/')

    @classmethod
    def starts_here(klass, stream):
        return klass.CHECK.match(stream.peek(10)) is not None

    def _parse(self, stream, indent):
        stream.next() # $
        stream.next() # {

        self.no = _parse_number(stream)

        stream.next() # /

        self.search = _parse_till_unescaped_char(stream, '/')[0]
        self.replace = _parse_till_unescaped_char(stream, '/')[0]
        self.options = _parse_till_closing_brace(stream)

    def __repr__(self):
        return "TransformationToken(%r,%r,%r,%r,%r)" % (
            self.start, self.end, self.no, self.search, self.replace
        )

class MirrorToken(Token):
    CHECK = re.compile(r'^\$\d+')

    @classmethod
    def starts_here(klass, stream):
        return klass.CHECK.match(stream.peek(10)) is not None

    def _parse(self, stream, indent):
        stream.next() # $
        self.no = _parse_number(stream)

    def __repr__(self):
        return "MirrorToken(%r,%r,%r)" % (
            self.start, self.end, self.no
        )

class EscapeCharToken(Token):
    @classmethod
    def starts_here(klass, stream, chars = '{}\$`'):
        cs = stream.peek(2)
        if len(cs) == 2 and cs[0] == '\\' and cs[1] in chars:
            return True

    def _parse(self, stream, indent):
        stream.next() # \
        self.initial_text = stream.next()

    def __repr__(self):
        return "EscapeCharToken(%r,%r,%r)" % (
            self.start, self.end, self.initial_text
        )

class ShellCodeToken(Token):
    @classmethod
    def starts_here(klass, stream):
        return stream.peek(1) == '`'

    def _parse(self, stream, indent):
        stream.next() # `
        self.code = _parse_till_unescaped_char(stream, '`')[0]

    def __repr__(self):
        return "ShellCodeToken(%r,%r,%r)" % (
            self.start, self.end, self.code
        )

class PythonCodeToken(Token):
    CHECK = re.compile(r'^`!p\s')

    @classmethod
    def starts_here(klass, stream):
        return klass.CHECK.match(stream.peek(4)) is not None

    def _parse(self, stream, indent):
        for i in range(3):
            stream.next() # `!p
        if stream.peek() in '\t ':
            stream.next()

        code = _parse_till_unescaped_char(stream, '`')[0]

        # Strip the indent if any
        if len(indent):
            lines = code.splitlines()
            self.code = lines[0] + '\n'
            self.code += '\n'.join([l[len(indent):]
                        for l in lines[1:]])
        else:
            self.code = code
        self.indent = indent

    def __repr__(self):
        return "PythonCodeToken(%r,%r,%r)" % (
            self.start, self.end, self.code
        )

class VimLCodeToken(Token):
    CHECK = re.compile(r'^`!v\s')

    @classmethod
    def starts_here(klass, stream):
        return klass.CHECK.match(stream.peek(4)) is not None

    def _parse(self, stream, indent):
        for i in range(4):
            stream.next() # `!v
        self.code = _parse_till_unescaped_char(stream, '`')[0]

    def __repr__(self):
        return "VimLCodeToken(%r,%r,%r)" % (
            self.start, self.end, self.code
        )

class EndOfTextToken(Token):
    def _parse(self, stream, indent):
        pass # Does nothing

    def __repr__(self):
        return "EndOfText(%r)" % self.end
# End: Tokens  }}}

__ALLOWED_TOKENS = [
    EscapeCharToken, VisualToken, TransformationToken, TabStopToken, MirrorToken,
    PythonCodeToken, VimLCodeToken, ShellCodeToken
]
def tokenize(text, indent, offset):
    stream = _TextIterator(text, offset)

    try:
        while True:
            done_something = False
            for t in __ALLOWED_TOKENS:
                if t.starts_here(stream):
                    yield t(stream, indent)
                    done_something = True
                    break
            if not done_something:
                stream.next()
    except StopIteration:
        yield EndOfTextToken(stream, indent)

