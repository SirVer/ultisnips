#!/usr/bin/env python3

"""A ${VISUAL} placeholder that will use the text that was last visually
selected and insert it here.

If there was no text visually selected, this will be the empty string.

"""

import re
import textwrap

from UltiSnips.indent_util import IndentUtil
from UltiSnips.text_objects.base import NoneditableTextObject
from UltiSnips.text_objects.transformation import TextObjectTransformation

_REPLACE_NON_WS = re.compile(r"[^ \t]")


class Visual(NoneditableTextObject, TextObjectTransformation):
    """See module docstring."""

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

        # Non-cooperative multiple inheritance: NoneditableTextObject and
        # TextObjectTransformation have incompatible __init__ signatures, so
        # we call each parent explicitly rather than using super().
        NoneditableTextObject.__init__(
            self, parent, token.start, token.end, token.initial_text
        )
        TextObjectTransformation.__init__(self, token)

    def _update(self, done, buf):
        if self._mode == "v":  # Normal selection.
            text = self._text
        else:  # Block selection or line selection.
            text_before = buf[self.start.line][: self.start.col]
            indent = _REPLACE_NON_WS.sub(" ", text_before)
            iu = IndentUtil()
            indent = iu.indent_to_spaces(indent)
            indent = iu.spaces_to_indent(indent)
            text = ""
            for idx, line in enumerate(textwrap.dedent(self._text).splitlines(True)):
                if idx != 0:
                    text += indent
                text += line
            text = text[:-1]  # Strip final '\n'

        text = self._transform(text)
        if self._snippet_has_m_option():
            # The `m` option strips trailing whitespace from every line at
            # launch, but ${VISUAL} content is materialized later in
            # _update; the indent we just prepended to empty visual lines
            # would survive as a bare-whitespace line. Match the `m`
            # contract by rstripping each line of the substituted content.
            # See #503.
            text = "\n".join(line.rstrip() for line in text.split("\n"))
        self.overwrite(buf, text)
        self._parent._del_child(self)

        return True

    def _snippet_has_m_option(self):
        """Walk up to the containing SnippetInstance and check the `m` option."""
        obj = self._parent
        while obj is not None:
            snippet = getattr(obj, "snippet", None)
            if snippet is not None:
                return snippet.has_option("m")
            obj = obj._parent
        return False
