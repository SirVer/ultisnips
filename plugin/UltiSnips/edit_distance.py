#!/usr/bin/env python
# encoding: utf-8

import heapq # TODO: overkill. Bucketing is better
from collections import defaultdict
import sys

# TODO: check test cases here. They are not up to date

from .debug import debug

def line_diffs(a, b, sline = 0):
    d = defaultdict(list)
    seen = defaultdict(lambda: sys.maxint)

    d[0] = [ (0,0,sline, ()) ]
    cost = 0
    while True:
        while len(d[cost]):
            x, y, line, what = d[cost].pop()

            if x == len(a) and y == len(b):
                # Find first span of changes in both buffers
                x_min, x_max = sys.maxint, -sys.maxint
                y_min, y_max = sys.maxint, -sys.maxint
                debug("what: %r" % (what,))
                for cmd,x,y in what:
                    if cmd == 'D':
                        x_min = min(x_min, x)
                        x_max = max(x_max, x)
                    elif cmd == 'I':
                        x_max = max(x_max, x-1 if x > 0 else 0)
                        x_min = min(x_min, x-1 if x > 0 else 0)
                        # y_min = min(y_min, line)
                        y_min = min(y_min, y-1 if y > 0 else 0)
                        y_max = max(y_max, y)
                    elif cmd == "M":
                        x_min = min(x_min, x)
                        x_max = max(x_max, x)
                        y_min = min(y_min, y)
                        y_max = max(y_max, y)

                return (x_min, x_max), (y_min, y_max)

            # TODO: line == y
            if x < len(a) and y < len(b) and len(a[x]) == len(b[y]) and \
                a[x] == b[y]: # Equal lines
                if seen[x+1,y+1] > cost:
                    seen[x+1,y+1] = cost
                    if x != y:
                        d[cost].append((x+1,y+1,line+1, what + (('M', x,y),))) # TODO: match only debug
                    else:
                        d[cost].append((x+1,y+1,line+1, what)) # TODO: match only debug
            if x < len(a): # Delete
                if seen[x+1,y] > cost + 1 + x:
                    seen[x+1,y] = cost + 1 + x
                    d[cost+1+x].append((x+1,y, line, what + (('D', x, y),)))
            if y < len(b): # Insert
                if seen[x,y+1] > cost + 1 + y:
                    seen[x,y+1] = cost + 1 + y
                    d[cost+1+y].append((x,y+1,line+1, what + (('I', x, y),)))
        cost += 1


def edit_script(a, b, sline = 0):
    d = defaultdict(list)
    seen = defaultdict(lambda: sys.maxint)

    d[0] = [ (0,0,sline, 0, ()) ]

    # TODO: needs some doku
    cost = 0
    D_COST = len(a)+len(b)
    I_COST = len(a)+len(b)
    while True:
        while len(d[cost]):
            #sumarized = [ compactify(what) for c, x, line, col, what in d[cost] ] # TODO: not needed
            #print "%r: %r" % (cost, sumarized)
            x, y, line, col, what = d[cost].pop()

            if a[x:] == b[y:]:
                #print "cost: %r" % (cost)
                return what

            if x < len(a) and y < len(b) and a[x] == b[y]:
                ncol = col + 1
                nline = line
                if a[x] == '\n':
                    ncol = 0
                    nline +=1
                lcost = cost + 1
                if (what and what[-1][0] == "D" and what[-1][1] == line and
                        what[-1][2] == col and a[x] != '\n'):
                    # Matching directly after a deletion should be as costly as DELETE + INSERT + a bit
                    lcost = (D_COST + I_COST)*1.5
                if seen[x+1,y+1] > lcost:
                    d[lcost].append((x+1,y+1, nline, ncol, what)) # TODO: slow!
                    seen[x+1,y+1] = lcost

            if y < len(b): # INSERT
                ncol = col + 1
                nline = line
                if b[y] == '\n':
                    ncol = 0
                    nline += 1
                if (what and what[-1][0] == "I" and what[-1][1] == nline and
                    what[-1][2]+len(what[-1][-1]) == col and b[y] != '\n' and
                    seen[x,y+1] > cost + (I_COST + ncol) // 2
                ):
                    seen[x,y+1] = cost + (I_COST + ncol) // 2
                    d[cost + (I_COST + ncol) // 2].append((x,y+1, line, ncol, what[:-1] + (("I", what[-1][1], what[-1][2], what[-1][-1] + b[y]),) ))
                elif seen[x,y+1] > cost + I_COST + ncol:
                    seen[x,y+1] = cost + I_COST + ncol
                    d[cost + ncol + I_COST].append((x,y+1, nline, ncol, what + (("I", line, col,b[y]),)))

            if x < len(a): # DELETE
                if (what and what[-1][0] == "D" and what[-1][1] == line and
                    what[-1][2] == col and a[x] != '\n' and what[-1][-1] != '\n' and
                    seen[x+1,y] > cost + D_COST // 2
                ):
                    seen[x+1,y] = cost + D_COST // 2
                    d[cost + D_COST // 2].append((x+1,y, line, col, what[:-1] + (("D",line, col, what[-1][-1] + a[x]),) ))
                elif seen[x+1,y] > cost + D_COST:
                    seen[x+1,y] = cost + D_COST
                    d[cost + D_COST].append((x+1,y, line, col, what + (("D",line, col, a[x]),) ))
        cost += 1

def transform(a, cmds):
    buf = a.split("\n")

    for cmd in cmds:
        ctype, line, col, char = cmd
        if ctype == "D":
            if char != '\n':
                buf[line] = buf[line][:col] + buf[line][col+len(char):]
            else:
                buf[line] = buf[line] + buf[line+1]
                del buf[line+1]
        elif ctype == "I":
            buf[line] = buf[line][:col] + char + buf[line][col:]
        buf = '\n'.join(buf).split('\n')
    return '\n'.join(buf)


import unittest

class _Base(object):
    def runTest(self):
        es = edit_script(self.a, self.b)
        tr = transform(self.a, es)
        self.assertEqual(self.b, tr)
        self.assertEqual(self.wanted, es)

class TestEmptyString(_Base, unittest.TestCase):
    a, b = "", ""
    wanted = ()

class TestAllMatch(_Base, unittest.TestCase):
    a, b = "abcdef", "abcdef"
    wanted = ()

class TestLotsaNewlines(_Base, unittest.TestCase):
    a, b = "Hello", "Hello\nWorld\nWorld\nWorld"
    wanted = (
        ("I", 0, 5, "\n"),
        ("I", 1, 0, "World"),
        ("I", 1, 5, "\n"),
        ("I", 2, 0, "World"),
        ("I", 2, 5, "\n"),
        ("I", 3, 0, "World"),
    )

class TestCrash(_Base, unittest.TestCase):
    a = 'hallo Blah mitte=sdfdsfsd\nhallo kjsdhfjksdhfkjhsdfkh mittekjshdkfhkhsdfdsf'
    b = 'hallo Blah mitte=sdfdsfsd\nhallo b mittekjshdkfhkhsdfdsf'
    wanted = (
        ("D", 1, 6, "kjsdhfjksdhfkjhsdfkh"),
        ("I", 1, 6, "b"),
    )

class TestRealLife(_Base, unittest.TestCase):
    a = 'hallo End Beginning'
    b = 'hallo End t'
    wanted = (
        ("D", 0, 10, "Beginning"),
        ("I", 0, 10, "t"),
    )

class TestRealLife1(_Base, unittest.TestCase):
    a = 'Vorne hallo Hinten'
    b = 'Vorne hallo  Hinten'
    wanted = (
        ("I", 0, 11, " "),
    )

class TestWithNewline(_Base, unittest.TestCase):
    a = 'First Line\nSecond Line'
    b = 'n'
    wanted = (
        ("D", 0, 0, "First Line"),
        ("D", 0, 0, "\n"),
        ("D", 0, 0, "Second Line"),
        ("I", 0, 0, "n"),
    )


class TestCheapDelete(_Base, unittest.TestCase):
    a = 'Vorne hallo Hinten'
    b = 'Vorne Hinten'
    wanted = (
        ("D", 0, 5, " hallo"),
    )

class TestNoSubstring(_Base, unittest.TestCase):
    a,b = "abc", "def"
    wanted = (
        ("D", 0, 0, "abc"),
        ("I", 0, 0, "def"),
    )
# TODO: quote the correct paper
#
# class TestPaperExample(_Base, unittest.TestCase):
    # a,b = "abcabba", "cbabac"
    # wanted = (
        # ("D", 0, 0, "ab"),
        # ("I", 0, 1, "b"),
        # ("D", 0, 4, "b"),
        # ("I", 0, 5, "c"),
    # )

class TestCommonCharacters(_Base, unittest.TestCase):
    a,b = "hasomelongertextbl", "hol"
    wanted = (
        ("D", 0, 1, "asomelongertextb"),
        ("I", 0, 1, "o"),
    )

class TestSKienaExample(_Base, unittest.TestCase):
    a, b = "thou shalt not", "you should not"
    wanted = (
        ('D', 0, 0, 'th'),
        ('I', 0, 0, 'y'),
        ('I', 0, 6, 'ou'),
        ('D', 0, 8, 'a'),
        ('D', 0, 9, 't'),
        ('I', 0, 9, 'd'),
    )

class TestUltiSnipsProblem(_Base, unittest.TestCase):
    a = "this is it this is it this is it"
    b = "this is it a this is it"
    wanted = (
        ("D", 0, 11, "this is it"),
        ("I", 0, 11, "a"),
    )

class MatchIsTooCheap(_Base, unittest.TestCase):
    a = "stdin.h"
    b = "s"
    wanted = (
        ("D", 0, 1, "tdin.h"),
    )

class MultiLine(_Base, unittest.TestCase):
    a = "hi first line\nsecond line first line\nsecond line world"
    b = "hi first line\nsecond line k world"

    wanted = (
        ("D", 1, 12, "first line"),
        ("D", 1, 12, "\n"),
        ("D", 1, 12, "second line"),
        ("I", 1, 12, "k"),
    )


if __name__ == '__main__':
   unittest.main()
   # k = TestEditScript()
   # unittest.TextTestRunner().run(k)



