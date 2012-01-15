#!/usr/bin/env python
# encoding: utf-8

import heapq # TODO: overkill. Bucketing is better
from collections import defaultdict

class GridPoint(object):
    """Docstring for GridPoint """

    __slots__ = ("parent", "cost",)

    def __init__(self, parent, cost):
        """@todo: to be defined

        :parent: @todo
        :cost: @todo
        """
        self._parent = parent
        self._cost = cost

def edit_script(a, b):
    d = defaultdict(list)

    d[0] = [ (0,0,0,0, ()) ]

    cost = 0
    while True:
        while len(d[cost]):
            y, x, nline, ncol, what = d[cost].pop()

            if x == len(a) and y == len(b):
                return what

            if x < len(a) and y < len(b) and a[x] == b[y]:
                ncol += 1
                if a[x] == '\n':
                    ncol = 0
                    nline += 1
                d[cost].append((y+1,x+1, nline, ncol, what))
            else:
                if x < len(a):
                    d[cost + 1].append((y,x+1, nline, ncol, what + (("D",nline, ncol),) ))
                if y < len(b):
                    oline, ocol = nline, ncol
                    ncol += 1
                    if b[y] == '\n':
                        ncol = 0
                        nline += 1
                    d[cost + 1].append((y+1,x, nline, ncol, what + (("I", oline, ocol,b[y]),)))
        cost += 1

def transform(a, cmds):
    buf = a.split("\n")

    for cmd in cmds:
        if cmd[0] == "D":
            line, col = cmd[1:]
            buf[line] = buf[line][:col] + buf[line][col+1:]
        elif cmd[0] == "I":
            line, col, char = cmd[1:]
            buf[line] = buf[line][:col] + char + buf[line][col:]
        buf = '\n'.join(buf).split('\n')
    return '\n'.join(buf)


import unittest

class _Base(object):
    def runTest(self):
        es = edit_script(self.a, self.b)
        tr = transform(self.a, es)
        self.assertEqual(self.b, tr)

class TestEmptyString(_Base, unittest.TestCase):
    a, b = "", ""

class TestAllMatch(_Base, unittest.TestCase):
    a, b = "abcdef", "abcdef"

class TestLotsaNewlines(_Base, unittest.TestCase):
    a, b = "Hello", "Hello\nWorld\nWorld\nWorld"

    # def test_all_match(self):
        # rv = edit_script("abcdef", "abcdef")
        # self.assertEqual("MMMMMM", rv)

    # def test_no_substr(self):
        # rv = edit_script("abc", "def")
        # self.assertEqual("SSS", rv)

    # def test_paper_example(self):
        # rv = edit_script("abcabba","cbabac")
        # self.assertEqual(rv, "SMDMMDMI")

    # def test_skiena_example(self):
        # rv = edit_script("thou shalt not", "you should not")
        # self.assertEqual(rv, "DSMMMMMISMSMMMM")
if __name__ == '__main__':
   unittest.main()
   # k = TestEditScript()
   # unittest.TextTestRunner().run(k)



