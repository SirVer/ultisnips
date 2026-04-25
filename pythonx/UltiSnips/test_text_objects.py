#!/usr/bin/env python3

"""Unit tests for the TextObject sort/comparison behaviour.

The vim module is mocked by pythonx/conftest.py.
"""

import unittest

from UltiSnips.position import Position
from UltiSnips.text_objects.base import TextObject


class _FakeParent:
    def __init__(self):
        self._children = []

    def _add_child(self, child):
        self._children.append(child)


class TextObjectSort_RuntimeCollisionFallsBackToOrigin(unittest.TestCase):
    """Two text objects that started at different source positions but
    later collapsed to the same runtime position must sort by source
    position (origin), not by set iteration order.

    Regression for https://github.com/SirVer/ultisnips/issues/1403: two
    `!p` blocks back-to-back (each initially zero-width after placement)
    had identical runtime positions and identical legacy tiebreakers, so
    `sorted(set(...))` fell back to set iteration order — non-deterministic
    in CPython. The producer block could run after the consumer, the
    convergence loop never re-ran the consumer, and the inter-block
    dependency silently dropped.
    """

    def test_runtime_tie_breaks_by_construction_position(self):
        parent = _FakeParent()
        # Two text objects parsed from different source positions ...
        first = TextObject(parent, Position(0, 5), Position(0, 10))
        second = TextObject(parent, Position(0, 10), Position(0, 20))
        # ... that later collapse to the same runtime span (e.g. both
        # `!p` blocks shrink to zero-width at col 5 after initial-text
        # placement).
        first._start.col = 5
        first._end.col = 5
        second._start.col = 5
        second._end.col = 5

        self.assertLess(first, second)
        self.assertLessEqual(first, second)
        self.assertFalse(second < first)

        # And, importantly, the result is the same regardless of which
        # order the underlying set hands them back.
        self.assertEqual([first, second], sorted({first, second}))
        self.assertEqual([first, second], sorted({second, first}))


class TextObjectSort_PositionBeatsOrigin(unittest.TestCase):
    """Construction origin is the *last* tiebreaker — earlier runtime
    positions still win."""

    def test_later_origin_with_earlier_runtime_start_sorts_first(self):
        parent = _FakeParent()
        from_late = TextObject(parent, Position(0, 50), Position(0, 50))
        from_early = TextObject(parent, Position(0, 5), Position(0, 5))
        # from_early was constructed second but its start.col is smaller.
        self.assertLess(from_early, from_late)
        self.assertEqual([from_early, from_late], sorted({from_late, from_early}))


if __name__ == "__main__":
    unittest.main()
