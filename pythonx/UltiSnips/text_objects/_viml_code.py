#!/usr/bin/env python
# encoding: utf-8


import UltiSnips._vim as _vim
from UltiSnips.text_objects._base import NoneditableTextObject

class VimLCode(NoneditableTextObject):
    def __init__(self, parent, token):
        self._code = token.code.replace("\\`", "`").strip()

        NoneditableTextObject.__init__(self, parent, token)

    def _update(self, done, not_done):
        self.overwrite(_vim.eval(self._code))
        return True

