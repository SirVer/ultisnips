#!/usr/bin/env python
# encoding: utf-8

import re

import UltiSnips._vim as _vim
from UltiSnips.util import IndentUtil
from UltiSnips.text_objects._transformation import TextObjectTransformation
from UltiSnips.text_objects._base import NoneditableTextObject

class Visual(NoneditableTextObject,TextObjectTransformation):
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
        if not self._text:
            self._text = token.alternative_text
            self._mode = "v"

        NoneditableTextObject.__init__(self, parent, token)
        TextObjectTransformation.__init__(self, token)

    def _update(self, done, not_done):
        if self._mode != "v":
            # Keep the indent for Line/Block Selection
            text_before = _vim.buf[self.start.line][:self.start.col]
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

        text = self._transform(text)
        self.overwrite(text)
        self._parent._del_child(self)

        return True


