#!/usr/bin/env python
# encoding: utf-8

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

    def gsub(self,pos):
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

import unittest

class _MPBase(object):
    def runTest(self):
        obj = Position(*self.obj)
        for pivot, diff, wanted in self.steps:
            obj.move(Position(*pivot), Position(*diff))
            self.assertEqual(Position(*wanted), obj)

class MovePosition_DelSameLine(_MPBase, unittest.TestCase):
    # hello wor*ld -> h*ld -> hl*ld
    obj = (0, 9)
    steps = (
        ((0, 1), (0, -8), (0, 1)),
        ((0, 1), (0, 1), (0, 2)),
    )
class MovePosition_DelSameLine1(_MPBase, unittest.TestCase):
    # hel*lo world -> hel*world -> hel*worl
    obj = (0,3)
    steps = (
        ((0, 4), (0, -3), (0,3)),
        ((0, 8), (0, -1), (0,3)),
    )
class MovePosition_InsSameLine1(_MPBase, unittest.TestCase):
    # hel*lo world -> hel*woresld
    obj = (0, 3)
    steps = (
        ((0, 4), (0, -3), (0, 3)),
        ((0, 6), (0, 2), (0, 3)),
        ((0, 8), (0, -1), (0, 3))
    )
class MovePosition_InsSameLine2(_MPBase, unittest.TestCase):
    # hello wor*ld -> helesdlo wor*ld
    obj = (0, 9)
    steps = (
        ((0, 3), (0, 3), (0, 12)),
    )

class MovePosition_DelSecondLine(_MPBase, unittest.TestCase):
    # hello world. sup   hello world.*a, was
    # *a, was            ach nix
    # ach nix
    obj = (1, 0)
    steps = (
        ((0, 12), (0, -4), (1, 0)),
        ((0, 12), (-1, 0), (0, 12)),
    )
class MovePosition_DelSecondLine1(_MPBase, unittest.TestCase):
    # hello world. sup
    # a, *was
    # ach nix
    # hello world.a*was
    # ach nix
    obj = (1, 3)
    steps = (
        ((0, 12), (0, -4), (1, 3)),
        ((0, 12), (-1, 0), (0, 15)),
        ((0, 12), (0, -3), (0, 12)),
        ((0, 12), (0,  1), (0, 13)),
    )
# TODO: what to do with these tests?
