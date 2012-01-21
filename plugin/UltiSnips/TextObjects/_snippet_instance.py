#!/usr/bin/env python
# encoding: utf-8

from UltiSnips.Geometry import Position

from ._base import TextObject
from ._parser import TOParser

class SnippetInstance(TextObject):
    """
    A Snippet instance is an instance of a Snippet Definition. That is,
    when the user expands a snippet, a SnippetInstance is created to
    keep track of the corresponding TextObjects. The Snippet itself is
    also a TextObject because it has a start an end
    """

    def __init__(self, parent, indent, initial_text, start, end, visual_content, last_re, globals):
        if start is None:
            start = Position(0,0)
        if end is None:
            end = Position(0,0)

        self.locals = {"match" : last_re}
        self.globals = globals
        self.visual_content = visual_content

        TextObject.__init__(self, parent, start, end, initial_text)

        TOParser(self, initial_text, indent).parse(True)

        self.do_edits()

    def replace_initital_text(self):
        def _place_initial_text(obj):
            obj.overwrite()

            for c in obj._childs:
                _place_initial_text(c)

        _place_initial_text(self)

    def _get_tabstop(self, requester, no):
        # SnippetInstances are completely self contained, therefore, we do not
        # need to ask our parent for Tabstops
        p = self._parent
        self._parent = None
        rv = TextObject._get_tabstop(self, requester, no)
        self._parent = p

        return rv

    def select_next_tab(self, backwards = False):
        if self._cts is None:
            return

        if backwards:
            cts_bf = self._cts

            res = self._get_prev_tab(self._cts)
            if res is None:
                self._cts = cts_bf
                return self._tabstops[self._cts]
            self._cts, ts = res
            return ts
        else:
            res = self._get_next_tab(self._cts)
            if res is None:
                self._cts = None
                return self._tabstops[0]
            else:
                self._cts, ts = res
                return ts

        return self._tabstops[self._cts]

