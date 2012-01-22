#!/usr/bin/env python
# encoding: utf-8

import vim

from UltiSnips.compatibility import as_unicode
from UltiSnips.text_objects._base import NoneditableTextObject

class VimLCode(NoneditableTextObject):
    def __init__(self, parent, token):
        self._code = token.code.replace("\\`", "`").strip()

        NoneditableTextObject.__init__(self, parent, token)

    def _update(self, done, not_done):
        self.overwrite(as_unicode(vim.eval(self._code)))
        return True

