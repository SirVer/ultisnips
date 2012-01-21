#!/usr/bin/env python
# encoding: utf-8

from ._base import NoneditableTextObject

class Mirror(NoneditableTextObject):
    """
    A Mirror object mirrors a TabStop that is, text is repeated here
    """
    def __init__(self, parent, tabstop, token):
        NoneditableTextObject.__init__(self, parent, token)

        self._ts = tabstop

    def _update(self, done, not_done):
        assert(not self._is_killed)
        if self._ts._is_killed:
            self.overwrite("")
            self._parent._del_child(self)
            return True

        if self._ts not in done:
            return False

        self.overwrite(self._get_text())
        return True

    def _get_text(self):
        return self._ts.current_text


