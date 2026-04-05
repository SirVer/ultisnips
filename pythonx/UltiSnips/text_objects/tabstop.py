#!/usr/bin/env python3

"""This is the most important TextObject.

A TabStop is were the cursor comes to rest when the user taps through
the Snippet.

"""

from UltiSnips.text_objects.base import EditableTextObject


class TabStop(EditableTextObject):
    """See module docstring."""

    def __init__(self, parent, token, start=None, end=None):
        if start is not None:
            self._number = token
            EditableTextObject.__init__(self, parent, start, end)
        else:
            self._number = token.number
            EditableTextObject.__init__(self, parent, token)
        parent._tabstops[self._number] = self  # pylint:disable=protected-access

    @property
    def number(self):
        """The tabstop number."""
        return self._number

    @property
    def is_killed(self):
        """True if this tabstop has been typed over and the user therefore can
        no longer jump to it."""
        return self._parent is None

    def __repr__(self):
        try:
            text = self.current_text
        except IndexError:
            text = "<err>"
        return f"TabStop({self.number},{self._start!r}->{self._end!r},{text!r})"
