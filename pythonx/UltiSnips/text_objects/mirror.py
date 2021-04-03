#!/usr/bin/env python3
# encoding: utf-8

"""A Mirror object contains the same text as its related tabstop."""

from UltiSnips.text_objects.base import NoneditableTextObject


class Mirror(NoneditableTextObject):

    """See module docstring."""

    def __init__(self, parent, tabstop, token):
        NoneditableTextObject.__init__(self, parent, token)
        self._ts = tabstop

    def _update(self, done, buf):
        if self._ts.is_killed:
            self.overwrite(buf, "")
            self._parent._del_child(self)  # pylint:disable=protected-access
            return True

        if self._ts not in done:
            return False

        self.overwrite(buf, self._get_text())
        return True

    def _get_text(self):
        """Returns the text used for mirroring.

        Overwritten by base classes.

        """
        return self._ts.current_text
