#!/usr/bin/env python
# encoding: utf-8

import unittest

import os.path as p, sys; sys.path.append(p.join(p.dirname(__file__), ".."))

from _diff import diff, guess_edit
from geometry import Position


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

# Test Guessing  {{{
class _BaseGuessing(object):
    def runTest(self):
        rv, es = guess_edit(self.initial_line, self.a, self.b, Position(*self.ppos), Position(*self.pos))
        self.assertEqual(rv, True)
        self.assertEqual(self.wanted, es)

class TestGuessing_Noop0(_BaseGuessing, unittest.TestCase):
    a, b = [], []
    initial_line = 0
    ppos, pos = (0, 6), (0, 7)
    wanted = ()

class TestGuessing_InsertOneChar(_BaseGuessing, unittest.TestCase):
    a, b = ["Hello  World"], ["Hello   World"]
    initial_line = 0
    ppos, pos = (0, 6), (0, 7)
    wanted = (
        ("I", 0, 6, " "),
    )
class TestGuessing_InsertOneChar1(_BaseGuessing, unittest.TestCase):
    a, b = ["Hello  World"], ["Hello   World"]
    initial_line = 0
    ppos, pos = (0, 7), (0, 8)
    wanted = (
        ("I", 0, 7, " "),
    )
class TestGuessing_BackspaceOneChar(_BaseGuessing, unittest.TestCase):
    a, b = ["Hello  World"], ["Hello World"]
    initial_line = 0
    ppos, pos = (0, 7), (0, 6)
    wanted = (
        ("D", 0, 6, " "),
    )
class TestGuessing_DeleteOneChar(_BaseGuessing, unittest.TestCase):
    a, b = ["Hello  World"], ["Hello World"]
    initial_line = 0
    ppos, pos = (0, 5), (0, 5)
    wanted = (
        ("D", 0, 5, " "),
    )

# End: Test Guessing  }}}

class _Base(object):
    def runTest(self):
        es = diff(self.a, self.b)
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

class TestCommonCharacters(_Base, unittest.TestCase):
    a,b = "hasomelongertextbl", "hol"
    wanted = (
        ("D", 0, 1, "asomelongertextb"),
        ("I", 0, 1, "o"),
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




