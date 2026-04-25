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


class TextObjectSort_SamePositionFallsBackToCreationOrder(unittest.TestCase):
    """Two text objects sharing start, end, and tiebreaker must sort in the
    order they were created.

    Regression for https://github.com/SirVer/ultisnips/issues/1403: two
    `!p` blocks back-to-back (each initially zero-width) had identical
    sort keys, so `sorted(set(...))` fell back to set iteration order —
    non-deterministic in CPython. The producer block could run after the
    consumer, the convergence loop never re-ran the consumer, and the
    inter-block dependency silently dropped.
    """

    def test_set_sorted_yields_creation_order(self):
        parent = _FakeParent()
        first = TextObject(parent, Position(0, 5), Position(0, 5))
        second = TextObject(parent, Position(0, 5), Position(0, 5))

        # Identical sort keys other than creation index — but creation
        # index is the trump card and should put first before second
        # regardless of how the input set iterates.
        self.assertLess(first, second)
        self.assertLessEqual(first, second)
        self.assertFalse(second < first)

        ordered = sorted({first, second})
        self.assertEqual([first, second], ordered)

        # Also true if we shove them into the set in the opposite order.
        ordered_rev = sorted({second, first})
        self.assertEqual([first, second], ordered_rev)


class TextObjectSort_PositionStillBeatsCreationOrder(unittest.TestCase):
    """Creation order is the *last* tiebreaker — earlier positions still win."""

    def test_later_creation_with_earlier_start_sorts_first(self):
        parent = _FakeParent()
        later = TextObject(parent, Position(0, 10), Position(0, 10))
        earlier = TextObject(parent, Position(0, 2), Position(0, 2))
        # earlier was created second but its start.col is smaller.
        self.assertLess(earlier, later)
        self.assertEqual([earlier, later], sorted({later, earlier}))


if __name__ == "__main__":
    unittest.main()
