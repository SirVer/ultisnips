#!/usr/bin/env python
# encoding: utf-8

__all__ = [ "Position" ]

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

    def move(self, pivot, diff):
        """pivot is the position of the first changed
        character, diff is how text after it moved"""
        if self < pivot: return
        if diff.line == 0:
            if self.line == pivot.line:
                self.col += diff.col
        elif diff.line > 0:
            if self.line == pivot.line:
                self.col += diff.col - pivot.col
            self.line += diff.line
        else:
            self.line += diff.line
            if self.line == pivot.line:
                self.col += - diff.col + pivot.col


    def __add__(self,pos):
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))

        return Position(self.line + pos.line, self.col + pos.col)

    def __sub__(self,pos):
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))
        return Position(self.line - pos.line, self.col - pos.col)

    def diff(self,pos):
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))
        if self.line == pos.line:
            return Position(0, self.col - pos.col)
        else:
            if self > pos:
                return Position(self.line - pos.line, self.col)
            else:
                return Position(self.line - pos.line, pos.col)
        return Position(self.line - pos.line, self.col - pos.col)

    def __eq__(self, other):
        return (self._line, self._col) == (other._line, other._col)
    def __ne__(self, other):
        return (self._line, self._col) != (other._line, other._col)
    def __lt__(self, other):
        return (self._line, self._col) < (other._line, other._col)
    def __le__(self, other):
        return (self._line, self._col) <= (other._line, other._col)

    def __repr__(self):
        return "(%i,%i)" % (self._line, self._col)

