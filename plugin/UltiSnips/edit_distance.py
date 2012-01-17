#!/usr/bin/env python
# encoding: utf-8

import heapq # TODO: overkill. Bucketing is better
from collections import defaultdict
import sys

def edit_script(a, b, sline = 0, scol = 0):
    d = defaultdict(list)
    seen = defaultdict(lambda: sys.maxint)

    d[0] = [ (0,0,sline,scol, ()) ]

    # TODO: needs some doku
    cost = 0
    DI_COST = len(a)+len(b)
    while True:
        while len(d[cost]):
            #sumarized = [ compactify(what) for c, x, line, col, what in d[cost] ] # TODO: not needed
            #print "%r: %r" % (cost, sumarized)
            x, y, line, col, what = d[cost].pop()

            if a[x:] == b[y:]: ## TODO: try out is
                #print "cost: %r" % (cost)
                return what

            if x < len(a) and y < len(b) and a[x] == b[y]:
                ncol = col + 1
                nline = line
                if a[x] == '\n':
                    ncol = 0
                    nline +=1
                if seen[x+1,y+1] > cost + 1:
                    d[cost+1].append((x+1,y+1, nline, ncol, what)) # TODO: slow!
                    seen[x+1,y+1] = cost + 1

            if y < len(b): # INSERT
                ncol = col + 1
                nline = line
                if b[y] == '\n':
                    ncol = 0
                    nline += 1
                if (what and what[-1][0] == "I" and what[-1][1] == nline and
                    what[-1][2]+len(what[-1][-1]) == col and b[y] != '\n' and
                    seen[x,y+1] > cost + (DI_COST + ncol) // 2
                ):
                    seen[x,y+1] = cost + (DI_COST + ncol) // 2
                    d[cost + (DI_COST + ncol) // 2].append((x,y+1, line, ncol, what[:-1] + (("I", what[-1][1], what[-1][2], what[-1][-1] + b[y]),) ))
                elif seen[x,y+1] > cost + DI_COST + ncol:
                    seen[x,y+1] = cost + DI_COST + ncol
                    d[cost + ncol + DI_COST].append((x,y+1, nline, ncol, what + (("I", line, col,b[y]),)))

            if x < len(a): # DELETE
                if (what and what[-1][0] == "D" and what[-1][1] == line and
                    what[-1][2] == col and a[x] != '\n' and
                    seen[x+1,y] > cost + DI_COST // 2
                ):
                    seen[x+1,y] = cost + DI_COST // 2
                    d[cost + DI_COST // 2].append((x+1,y, line, col, what[:-1] + (("D",line, col, what[-1][-1] + a[x]),) ))
                elif seen[x+1,y] > cost + DI_COST:
                    seen[x+1,y] = cost + DI_COST
                    d[cost + DI_COST].append((x+1,y, line, col, what + (("D",line, col, a[x]),) ))
        cost += 1

def transform(a, cmds):
    buf = a.split("\n")

    for cmd in cmds:
        ctype, line, col, char = cmd
        if ctype == "D":
            buf[line] = buf[line][:col] + buf[line][col+len(char):]
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
class TestPaperExample(_Base, unittest.TestCase):
    a,b = "abcabba", "cbabac"
    wanted = (
        ("D", 0, 0, "ab"),
        ("I", 0, 1, "b"),
        ("D", 0, 4, "b"),
        ("I", 0, 5, "c"),
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
        ("D", 0, 0, "stdin.h"),
        ("I", 0, 0, "s"),
    )

if __name__ == '__main__':
   unittest.main()
   # k = TestEditScript()
   # unittest.TextTestRunner().run(k)



