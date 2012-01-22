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
            self._no = token
            EditableTextObject.__init__(self, parent, start, end)
        else:
            self._no = token.no
            EditableTextObject.__init__(self, parent, token)
        parent._tabstops[self._no] = self

    @property
    def no(self):
        return self._no

    @property
    def is_killed(self):
        return self._parent is None


