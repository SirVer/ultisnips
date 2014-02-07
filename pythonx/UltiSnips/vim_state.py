#!/usr/bin/env python
# encoding: utf-8

"""Some classes to conserve Vim's state for comparing over time."""

from collections import deque

from UltiSnips.compatibility import as_unicode, byte2col
from UltiSnips.geometry import Position
import UltiSnips._vim as _vim

class VimPosition(Position):
    """Represents the current position in the buffer, together with some status
    variables that might change our decisions down the line."""

    def __init__(self):
        pos = _vim.buf.cursor
        self._mode = _vim.eval("mode()")
        Position.__init__(self, pos.line, pos.col)

    @property
    def mode(self):
        """Returns the mode() this position was created."""
        return self._mode

class VimState(object):
    """Caches some state information from Vim to better guess what editing
    tasks the user might have done in the last step."""

    def __init__(self):
        self._poss = deque(maxlen=5)
        self._lvb = None

    def remember_position(self):
        """Remember the current position as a previous pose."""
        self._poss.append(VimPosition())

    def remember_buffer(self, to):
        """Remember the content of the buffer and the position."""
        self._lvb = _vim.buf[to.start.line:to.end.line+1]
        self._lvb_len = len(_vim.buf)
        self.remember_position()

    @property
    def diff_in_buffer_length(self):
        """Returns the difference in the length of the current buffer compared
        to the remembered."""
        return len(_vim.buf) - self._lvb_len

    @property
    def pos(self):
        """The last remembered position."""
        return self._poss[-1]

    @property
    def ppos(self):
        """The second to last remembered position."""
        return self._poss[-2]

    @property
    def remembered_buffer(self):
        """The content of the remembered buffer."""
        return self._lvb[:]

class VisualContentPreserver(object):
    """Saves the current visual selection and the selection mode it was done in
    (e.g. line selection, block selection or regular selection.)"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Forget the preserved state."""
        self._mode = ""
        self._text = as_unicode("")

    def conserve(self):
        """Save the last visual selection ond the mode it was made in."""
        sl, sbyte = map(int,
                (_vim.eval("""line("'<")"""), _vim.eval("""col("'<")""")))
        el, ebyte = map(int,
                (_vim.eval("""line("'>")"""), _vim.eval("""col("'>")""")))
        sc = byte2col(sl, sbyte - 1)
        ec = byte2col(el, ebyte - 1)
        self._mode = _vim.eval("visualmode()")

        _vim_line_with_eol = lambda ln: _vim.buf[ln] + '\n'

        if sl == el:
            text = _vim_line_with_eol(sl-1)[sc:ec+1]
        else:
            text = _vim_line_with_eol(sl-1)[sc:]
            for cl in range(sl, el-1):
                text += _vim_line_with_eol(cl)
            text += _vim_line_with_eol(el-1)[:ec+1]
        self._text = text

    @property
    def text(self):
        """The conserved text."""
        return self._text

    @property
    def mode(self):
        """The conserved visualmode()."""
        return self._mode
