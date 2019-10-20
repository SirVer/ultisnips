#!/usr/bin/env python
# encoding: utf-8

"""Utilities to deal with text."""


def unescape(text):
    """Removes '\\' escaping from 'text'."""
    rv = ""
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == "\\":
            rv += text[i + 1]
            i += 1
        else:
            rv += text[i]
        i += 1
    return rv


def escape(text, chars):
    """Escapes all characters in 'chars' in text using backspaces."""
    rv = ""
    for char in text:
        if char in chars:
            rv += "\\"
        rv += char
    return rv


def fill_in_whitespace(text):
    """Returns 'text' with escaped whitespace replaced through whitespaces."""
    text = text.replace(r"\n", "\n")
    text = text.replace(r"\t", "\t")
    text = text.replace(r"\r", "\r")
    text = text.replace(r"\a", "\a")
    text = text.replace(r"\b", "\b")
    return text


def head_tail(line):
    """Returns the first word in 'line' and the rest of 'line' or None if the
    line is too short."""
    generator = (t.strip() for t in line.split(None, 1))
    head = next(generator).strip()
    tail = ""
    try:
        tail = next(generator).strip()
    except StopIteration:
        pass
    return head, tail


class LineIterator(object):

    """Convenience class that keeps track of line numbers in files."""

    def __init__(self, text):
        self._line_index = -1
        self._lines = list(text.splitlines(True))

    def __iter__(self):
        return self

    def __next__(self):
        """Returns the next line."""
        if self._line_index + 1 < len(self._lines):
            self._line_index += 1
            return self._lines[self._line_index]
        raise StopIteration()

    next = __next__  # for python2

    @property
    def line_index(self):
        """The 1 based line index in the current file."""
        return self._line_index + 1

    def peek(self):
        """Returns the next line (if there is any, otherwise None) without
        advancing the iterator."""
        try:
            return self._lines[self._line_index + 1]
        except IndexError:
            return None
