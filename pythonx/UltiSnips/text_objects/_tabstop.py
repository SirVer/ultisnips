#!/usr/bin/env python
# encoding: utf-8

from UltiSnips.text_objects._base import EditableTextObject

__all__ = ['EditableTextObject']

class TabStop(EditableTextObject):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, parent, token, start = None, end = None):
        if start is not None:
            self._number = token
            EditableTextObject.__init__(self, parent, start, end)
        else:
            self._number = token.number
            EditableTextObject.__init__(self, parent, token)
        parent._tabstops[self._number] = self

    @property
    def number(self):
        return self._number

    @property
    def is_killed(self):
        return self._parent is None
