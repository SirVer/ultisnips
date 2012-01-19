#!/usr/bin/env python
# encoding: utf-8

from ._base import NoneditableTextObject

class Visual(NoneditableTextObject):
    """
    A ${VISUAL} placeholder that will use the text that was last visually
    selected and insert it here. If there was no text visually selected,
    this will be the empty string
    """
    def __init__(self, parent, token):
        # TODO: rework this: get indent directly from vim buffer and
        # only update once.

        # Find our containing snippet for visual_content
        snippet = parent
        while snippet:
            try:
                self._visual_content = snippet.visual_content.splitlines(True)
                break
            except AttributeError:
                snippet = snippet._parent

        text = ""
        for idx, line in enumerate(self._visual_content):
            text += token.leading_whitespace
            text += line

        self._text = text

        NoneditableTextObject.__init__(self, parent, token, initial_text = self._text)

    def _really_updateman(self, done, not_done):
        self.overwrite(self._text)
        self._parent._del_child(self)
        return True


