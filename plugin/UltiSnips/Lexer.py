#!/usr/bin/env python
# encoding: utf-8

"""
Not really a Lexer in the classical sense, but code to hack Snippet Definitions
into Logical Units called Tokens.
"""

import string
import re

from Geometry import Position

# TODO: review this file

# Helper Classes  {{{
class _TextIterator(object):
    def __init__(self, text):
        self._text = text
        self._line = 0
        self._col = 0

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
        try:
            return self._text[self._idx:self._idx + count]
        except IndexError:
            return None

    @property
    def idx(self):
        return self._idx # TODO: does this need to be exposed?

    @property
    def pos(self):
        return Position(self._line, self._col)

    @property
    def exhausted(self):
        return self._idx >= len(self._text)
# End: Helper Classes  }}}
# Helper functions  {{{
def _parse_number(stream):
    # TODO: document me
    rv = ""
    while stream.peek() in string.digits:
        rv += stream.next()

    return int(rv)

def _parse_till_closing_brace(stream):
    # TODO: document me, this also eats the closing brace
    rv = ""
    in_braces = 1
    while True:
        if EscapeCharToken.check(stream, '{}'):
            rv += stream.next() + stream.next()
        else:
            c = stream.next()
            if c == '{': in_braces += 1
            elif c == '}': in_braces -= 1
            if in_braces == 0:
                break
            rv += c
    return rv


# TODO: the functionality of some of these functions are quite
# similar. Somekind of next_matching
def _parse_till_unescaped_char(stream, char):
    # TODO: document me, this also eats the closing slash
    rv = ""
    in_braces = 1
    while True:
        if EscapeCharToken.check(stream, char):
            rv += stream.next() + stream.next()
        else:
            c = stream.next()
            if c == char:
                break
            rv += c
    return rv
# End: Helper functions  }}}

# Tokens  {{{
class Token(object):
    def __init__(self, gen, indent):
        self.initial_text = ""
        self.start = gen.pos
        self._parse(gen, indent)
        self.end = gen.pos

class TabStopToken(Token):
    CHECK = re.compile(r'^\${\d+[:}]')

    @classmethod
    def check(klass, stream):
        # TODO: bad name for function
        return klass.CHECK.match(stream.peek(10)) != None

    def _parse(self, stream, indent):
        stream.next() # $
        stream.next() # {

        self.no = _parse_number(stream)

        if stream.peek() is ":":
            stream.next()
        self.initial_text = _parse_till_closing_brace(stream)

    def __repr__(self):
        return "TabStopToken(%r,%r,%r,%r)" % (
            self.start, self.end, self.no, self.initial_text
        )

class TransformationToken(Token):
    CHECK = re.compile(r'^\${\d+\/')

    @classmethod
    def check(klass, stream):
        # TODO: bad name for function
        return klass.CHECK.match(stream.peek(10)) != None

    def _parse(self, stream, indent):
        stream.next() # $
        stream.next() # {

        self.no = _parse_number(stream)

        stream.next() # /

        self.search = _parse_till_unescaped_char(stream, '/')
        self.replace = _parse_till_unescaped_char(stream, '/')
        self.options = _parse_till_closing_brace(stream)

    def __repr__(self):
        return "TransformationToken(%r,%r,%r,%r,%r)" % (
            self.start, self.end, self.no, self.search, self.replace
        )

class MirrorToken(Token):
    CHECK = re.compile(r'^\$\d+')

    @classmethod
    def check(klass, stream):
        # TODO: bad name for function
        return klass.CHECK.match(stream.peek(10)) != None

    def _parse(self, stream, indent):
        # TODO: why not parse number?
        self.no = ""
        stream.next() # $
        while not stream.exhausted and stream.peek() in string.digits:
            self.no += stream.next()
        self.no = int(self.no)

    def __repr__(self):
        return "MirrorToken(%r,%r,%r)" % (
            self.start, self.end, self.no
        )

class EscapeCharToken(Token):
    @classmethod
    def check(klass, stream, chars = '{}\$`'):
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
    def check(klass, stream):
        return stream.peek(1) == '`'

    def _parse(self, stream, indent):
        stream.next() # `
        self.code = _parse_till_unescaped_char(stream, '`')

    # TODO: get rid of those __repr__ maybe
    def __repr__(self):
        return "ShellCodeToken(%r,%r,%r)" % (
            self.start, self.end, self.code
        )

# TODO: identical to VimLCodeToken
class PythonCodeToken(Token):
    CHECK = re.compile(r'^`!p\s')

    @classmethod
    def check(klass, stream):
        return klass.CHECK.match(stream.peek(4)) is not None

    def _parse(self, stream, indent):
        for i in range(3):
            stream.next() # `!p
        if stream.peek() in '\t ':
            stream.next()

        code = _parse_till_unescaped_char(stream, '`')

        # TODO: stupid to pass the indent down even if only python
        # needs it. Stupid to indent beforehand.

        # Strip the indent if any
        if len(indent):
            lines = code.splitlines()
            self.code = lines[0] + '\n'
            self.code += '\n'.join([l[len(indent):]
                        for l in lines[1:]])
        else:
            self.code = code
        self.indent = indent

    # TODO: get rid of those __repr__ maybe
    def __repr__(self):
        return "PythonCodeToken(%r,%r,%r)" % (
            self.start, self.end, self.code
        )


class VimLCodeToken(Token):
    CHECK = re.compile(r'^`!v\s')

    @classmethod
    def check(klass, stream):
        return klass.CHECK.match(stream.peek(4)) is not None

    def _parse(self, stream, indent):
        for i in range(4):
            stream.next() # `!v
        self.code = _parse_till_unescaped_char(stream, '`')

    def __repr__(self):
        return "VimLCodeToken(%r,%r,%r)" % (
            self.start, self.end, self.code
        )
# End: Tokens  }}}

__ALLOWED_TOKENS = [
    EscapeCharToken, TransformationToken, TabStopToken, MirrorToken,
    PythonCodeToken, VimLCodeToken, ShellCodeToken
]

def tokenize(text, indent):
    stream = _TextIterator(text)

    while True:
        done_something = False
        for t in __ALLOWED_TOKENS:
            if t.check(stream):
                yield t(stream, indent)
                done_something = True
                break
        if not done_something:
            stream.next()


