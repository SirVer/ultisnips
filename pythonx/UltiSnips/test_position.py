#!/usr/bin/env python
# encoding: utf-8

# pylint: skip-file

import unittest

from position import Position


class _MPBase:
    def runTest(self):
        obj = Position(*self.obj)
        for pivot, delta, wanted in self.steps:
            obj.move(Position(*pivot), Position(*delta))
            self.assertEqual(Position(*wanted), obj)


class MovePosition_DelSameLine(_MPBase, unittest.TestCase):
    # hello wor*ld -> h*ld -> hl*ld
    obj = (0, 9)
    steps = (((0, 1), (0, -8), (0, 1)), ((0, 1), (0, 1), (0, 2)))


class MovePosition_DelSameLine1(_MPBase, unittest.TestCase):
    # hel*lo world -> hel*world -> hel*worl
    obj = (0, 3)
    steps = (((0, 4), (0, -3), (0, 3)), ((0, 8), (0, -1), (0, 3)))


class MovePosition_InsSameLine1(_MPBase, unittest.TestCase):
    # hel*lo world -> hel*woresld
    obj = (0, 3)
    steps = (
        ((0, 4), (0, -3), (0, 3)),
        ((0, 6), (0, 2), (0, 3)),
        ((0, 8), (0, -1), (0, 3)),
    )


class MovePosition_InsSameLine2(_MPBase, unittest.TestCase):
    # hello wor*ld -> helesdlo wor*ld
    obj = (0, 9)
    steps = (((0, 3), (0, 3), (0, 12)),)


class MovePosition_DelSecondLine(_MPBase, unittest.TestCase):
    # hello world. sup   hello world.*a, was
    # *a, was            ach nix
    # ach nix
    obj = (1, 0)
    steps = (((0, 12), (0, -4), (1, 0)), ((0, 12), (-1, 0), (0, 12)))


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
        ((0, 12), (0, 1), (0, 13)),
    )


if __name__ == "__main__":
    unittest.main()
