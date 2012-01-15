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

    heap = [ (0,0,0,"") ]

    while True:
        cost, y, x,what = heapq.heappop(heap)

        if x == len(a) and y == len(b):
            return what

        if x < len(a) and y < len(b) and a[x] == b[y]:
            heapq.heappush(heap, (cost, y+1,x+1, what + "M"))
        else:
            if x < len(a) and y < len(b):
                heapq.heappush(heap, (cost + 1, y+1, x+1, what + "S"))
            if x < len(a):
                heapq.heappush(heap, (cost + 1, y, x+1, what + "D"))
            if y < len(b):
                heapq.heappush(heap, (cost + 1, y+1, x, what + "I"))


import unittest

class TestEditScript(unittest.TestCase):
    def test_empty_string(self):
        rv = edit_script("","")
        self.assertEqual(rv, "")

    def test_all_match(self):
        rv = edit_script("abcdef", "abcdef")
        self.assertEqual("MMMMMM", rv)

    def test_no_substr(self):
        rv = edit_script("abc", "def")
        self.assertEqual("SSS", rv)

    def test_paper_example(self):
        rv = edit_script("abcabba","cbabac")
        self.assertEqual(rv, "SMDMMDMI")

    def test_skiena_example(self):
        rv = edit_script("thou shalt not", "you should not")
        self.assertEqual(rv, "DSMMMMMISMSMMMM")
if __name__ == '__main__':
   unittest.main()
   # k = TestEditScript()
   # unittest.TextTestRunner().run(k)



