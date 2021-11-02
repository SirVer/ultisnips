#!/usr/bin/env python3
# encoding: utf-8

"""Implements `!v ` VimL interpolation."""

from UltiSnips import vim_helper
from UltiSnips.text_objects.base import NoneditableTextObject


class VimLCode(NoneditableTextObject):

    """See module docstring."""

    def __init__(self, parent, token):
        NoneditableTextObject.__init__(self, parent, token)
        self._code = token.code.replace("\\`", "`").strip()

    def _update(self, todo, buf):
        self.overwrite(buf, vim_helper.eval(self._code))
        return True
