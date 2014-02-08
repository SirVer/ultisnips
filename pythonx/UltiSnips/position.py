#!/usr/bin/env python
# encoding: utf-8

"""Represents a Position in a text file: (0 based line index, 0 based column
index) and provides methods for moving them around."""

class Position(object):
    """See module docstring."""

    def __init__(self, line, col):
        self.line = line
        self.col = col

    def move(self, pivot, delta):
        """'pivot' is the position of the first changed character, 'delta' is
        how text after it moved"""
        if self < pivot:
            return
        if delta.line == 0:
            if self.line == pivot.line:
                self.col += delta.col
        elif delta.line > 0:
            if self.line == pivot.line:
                self.col += delta.col - pivot.col
            self.line += delta.line
        else:
            self.line += delta.line
            if self.line == pivot.line:
                self.col += - delta.col + pivot.col

    def delta(self, pos):
        """Returns the difference that the cursor must move to come from 'pos'
        to us."""
        assert isinstance(pos, Position)
        if self.line == pos.line:
            return Position(0, self.col - pos.col)
        else:
            if self > pos:
                return Position(self.line - pos.line, self.col)
            else:
                return Position(self.line - pos.line, pos.col)
        return Position(self.line - pos.line, self.col - pos.col)

    def __add__(self, pos):
        assert isinstance(pos, Position)
        return Position(self.line + pos.line, self.col + pos.col)

    def __sub__(self, pos):
        assert isinstance(pos, Position)
        return Position(self.line - pos.line, self.col - pos.col)

    def __eq__(self, other):
        return (self.line, self.col) == (other.line, other.col)

    def __ne__(self, other):
        return (self.line, self.col) != (other.line, other.col)

    def __lt__(self, other):
        return (self.line, self.col) < (other.line, other.col)

    def __le__(self, other):
        return (self.line, self.col) <= (other.line, other.col)

    def __repr__(self):
        return "(%i,%i)" % (self.line, self.col)
