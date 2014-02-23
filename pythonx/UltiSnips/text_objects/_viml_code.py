#!/usr/bin/env python
# encoding: utf-8

"""Implements `!v ` VimL interpolation."""

from UltiSnips import _vim
from UltiSnips.text_objects._base import NoneditableTextObject

class VimLCode(NoneditableTextObject):
    """See module docstring."""
    def __init__(self, parent, token):
        self._code = token.code.replace("\\`", "`").strip()

        NoneditableTextObject.__init__(self, parent, token)

    def _update(self, done):
        self.overwrite(_vim.eval(self._code))
        return True
