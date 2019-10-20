#!/usr/bin/env python
# encoding: utf-8

"""Implements `!v ` VimL interpolation."""

from UltiSnips import vim_helper
from UltiSnips.text_objects.base import NoneditableTextObject


class VimLCode(NoneditableTextObject):

    """See module docstring."""

    def __init__(self, parent, token):
        self._code = token.code.replace("\\`", "`").strip()

        NoneditableTextObject.__init__(self, parent, token)

    def _update(self, done, buf):
        self.overwrite(buf, vim_helper.eval(self._code))
        return True
