#!/usr/bin/env python
# encoding: utf-8

from ._base import TextObject

__all__ = [ 'TabStop']

class TabStop(TextObject):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, parent, token, start = None, end = None):
        if start is not None:
            self._no = token
            TextObject.__init__(self, parent, start, end)
        else:
            TextObject.__init__(self, parent, token)
            self._no = token.no

        parent._tabstops[self._no] = self

    def no(self):
        return self._no
    no = property(no)

