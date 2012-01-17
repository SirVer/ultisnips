#!/usr/bin/env python
# encoding: utf-8

from UltiSnips.Compatibility import CheapTotalOrdering # TODO: no longer in use

__all__ = [ "Position", "Span" ]

class Position(object):
    def __init__(self, line, col):
        self.line = line
        self.col = col

    def col():
        def fget(self):
            return self._col
        def fset(self, value):
            self._col = value
        return locals()
    col = property(**col())

    def line():
        doc = "Zero base line numbers"
        def fget(self):
            return self._line
        def fset(self, value):
            self._line = value
        return locals()
    line = property(**line())

    def __add__(self,pos):
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))

        return Position(self.line + pos.line, self.col + pos.col)

    def __sub__(self,pos): # TODO: is this really true?
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))

        return Position(self.line - pos.line, self.col - pos.col)

    def __eq__(self, other):
        return (self._line, self._col) == (other._line, other._col)
    def __lt__(self, other):
        return (self._line, self._col) < (other._line, other._col)
    def __le__(self, other):
        return (self._line, self._col) <= (other._line, other._col)

    def __repr__(self):
        return "(%i,%i)" % (self._line, self._col)

class Span(object):
    def __init__(self, start, end):
        self._s = start
        self._e = end

    def __contains__(self, pos):
        return self._s <= pos <= self._e

    def start():
        def fget(self):
            return self._s
        def fset(self, value):
            self._s = value
        return locals()
    start = property(**start())

    def end():
        def fget(self):
            return self._e
        def fset(self, value):
            self._e = value
        return locals()
    end = property(**end())

    def __repr__(self):
        return "(%s -> %s)" % (self._s, self._e)

