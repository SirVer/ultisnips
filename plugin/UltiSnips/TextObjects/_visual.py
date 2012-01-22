#!/usr/bin/env python
# encoding: utf-8

import re

import vim

from UltiSnips.Compatibility import as_unicode
from UltiSnips.Util import IndentUtil
from UltiSnips.TextObjects._base import NoneditableTextObject

class Visual(NoneditableTextObject):
    """
    A ${VISUAL} placeholder that will use the text that was last visually
    selected and insert it here. If there was no text visually selected,
    this will be the empty string
    """
    __REPLACE_NON_WS = re.compile(r"[^ \t]")

    def __init__(self, parent, token):
        # Find our containing snippet for visual_content
        snippet = parent
        while snippet:
            try:
                self._text = snippet.visual_content.text
                self._mode = snippet.visual_content.mode
                break
            except AttributeError:
                snippet = snippet._parent

        NoneditableTextObject.__init__(self, parent, token)

    def _update(self, done, not_done):
        if self._mode != "v":
            # Keep the indent for Line/Block Selection
            text_before = as_unicode(vim.current.buffer[self.start.line])[:self.start.col]
            indent = self.__REPLACE_NON_WS.sub(" ", text_before)
            iu = IndentUtil()
            indent = iu.indent_to_spaces(indent)
            indent = iu.spaces_to_indent(indent)
            text = ""
            for idx, line in enumerate(self._text.splitlines(True)):
                if idx != 0:
                    text += indent
                text += line
            text = text[:-1] # Strip final '\n'
        else:
            text = self._text

        self.overwrite(text)
        self._parent._del_child(self)
        return True


