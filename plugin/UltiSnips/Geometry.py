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

    def copy(self):
        return Position(self._line, self._col)

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

    def gsub(self,pos): # TODO: is this really true?
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))
        if self.line == pos.line:
            return Position(0, self.col - pos.col)
        else:
            #if self > pos: # Idea: self + delta = pos
            if self > pos:
                return Position(self.line - pos.line, self.col)
            else:
                return Position(self.line - pos.line, pos.col)
            # else: return Position(self.line - pos.line, -self.col)

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

def _move(obj, pivot, diff):
    """pivot is the position of the first changed
    character, diff is how text after it moved"""
    if obj < pivot: return
    # TODO: test >= test here again
    if diff.line == 0:
        if obj.line == pivot.line:
            obj.col += diff.col
    elif diff.line > 0:
        if obj.line == pivot.line:
            obj.col += diff.col - pivot.col
        obj.line += diff.line
    else:
        obj.line += diff.line
        if obj.line == pivot.line:
            obj.col += - diff.col + pivot.col

class _MPBase(object):
    def runTest(self):
        obj = Position(*self.obj)
        for pivot, diff, wanted in self.steps:
            _move(obj, Position(*pivot), Position(*diff))
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

class RandomTest1(_MPBase, unittest.TestCase):
    a = 'cbaca\nabccAc\nbc'
    b = 'Aba\naca\nab'

    'Aba\naca\nabccAc\nbc'
    obj = (1,4)
    steps = (
        ((0, 0), (0, -1), (1, 4)),
        ((0, 0), (0,  1), (1, 4)),
        ((0, 3), (1, -3), (2, 4)),
        ((1, 0), (0,  1), (2, 4)),
        ((2, 2),(-1, -2), (0, 1)),
    )

from edit_distance import transform, edit_script
import random, string

class RandomTests(unittest.TestCase):
    def runTest(self):
        nlines = random.randint(1, 3)
        def make_random_text():
            text =[]
            for i in range(nlines):
                ncols = random.randint(1,5)
                text.append(''.join(random.choice("abc") for i in range(ncols)))
            lidx = random.randint(0, len(text)-1)
            cidx = random.randint(0, len(text[lidx])-1)
            text[lidx] = text[lidx][:cidx] + 'A' + text[lidx][cidx:]

            return '\n'.join(text), (lidx, cidx)

        def find_A(txt):
            idx = txt.find('A')
            line_idx = txt[:idx].count("\n")
            return line_idx, txt.split("\n")[line_idx].find('A')

        txt, initial_pos = make_random_text()
        txt2 = make_random_text()[0]
        self.assertEqual(find_A(txt), initial_pos)
        print "txt: %r, txt2: %r" % (txt, txt2)

        obj = Position(*initial_pos)
        for cmd in edit_script(txt, txt2):
            ctype, line, col, text = cmd

            if ctype == 'D':
                if text == "\n":
                    delta = Position(-1, 0)
                else:
                    delta = Position(0, -len(text))
            else:
                if text == "\n":
                    delta = Position(1, 0)
                else:
                    delta = Position(0, len(text))

            txt = transform(txt, (cmd,))
            _move(obj, Position(line, col), delta)

            # Apos = Position(*find_A(txt))
            # self.assertEqual(Apos.line, obj.line)
            # if Apos.col != -1:
                # self.assertEqual(Apos.col, obj.col)

        self.assertEqual(txt, txt2)
        Apos = Position(*find_A(txt))
        self.assertEqual(Apos, obj)

        print "line: %r, col: %r" % (line, col)



if __name__ == '__main__':
   # unittest.main()
   k = RandomTest1()
   unittest.TextTestRunner().run(k)

