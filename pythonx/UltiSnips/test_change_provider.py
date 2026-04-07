#!/usr/bin/env python3

"""Tests for change_provider helper functions.

The change providers themselves require Vim/Neovim and are tested via
the integration test suite (test_all.py).  This file tests the pure-Python
helper _guess_edit_with_trimming which is the shared edit detection logic.
"""

import unittest

from UltiSnips.diff import guess_edit
from UltiSnips.position import Position


class _MockPosition(Position):
    def __init__(self, line, col, mode="n"):
        super().__init__(line, col)
        self.mode = mode


class _MockVimState:
    def __init__(self, ppos, pos):
        self.ppos = _MockPosition(*ppos)
        self.pos = _MockPosition(*pos)


class TestGuessEditWithTrimming(unittest.TestCase):
    """Verify that guess_edit handles common editing patterns."""

    def _guess(self, initial, old, new, ppos, pos):
        vs = _MockVimState(ppos, pos)
        rv, es = guess_edit(initial, old, new, vs)
        return rv, es

    def test_single_char_insert(self):
        rv, es = self._guess(0, ["hello"], ["helxlo"], (0, 3), (0, 4))
        self.assertTrue(rv)
        self.assertEqual(es, (("I", 0, 3, "x"),))

    def test_backspace(self):
        rv, es = self._guess(0, ["hello"], ["helo"], (0, 4), (0, 3))
        self.assertTrue(rv)
        self.assertEqual(es, (("D", 0, 3, "l"),))

    def test_carriage_return(self):
        rv, es = self._guess(0, ["hello"], ["hel", "lo"], (0, 3), (1, 0))
        self.assertTrue(rv)
        self.assertEqual(es, (("I", 0, 3, "\n"),))

    def test_line_delete(self):
        rv, es = self._guess(0, ["a", "b", "c"], ["a", "c"], (1, 0), (1, 0))
        self.assertTrue(rv)
        self.assertEqual(es, [("D", 1, 0, "b"), ("D", 1, 0, "\n")])


if __name__ == "__main__":
    unittest.main()
