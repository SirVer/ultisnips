#!/usr/bin/env python
# encoding: utf-8

from collections import deque

from UltiSnips.geometry import Position
import UltiSnips._vim as _vim

class VimPosition(Position):
    def __init__(self):
        """Represents the current position in the buffer, together with some
        status variables that might change our decisions down the line. """
        pos = _vim.buf.cursor
        self._mode = _vim.eval("mode()")
        Position.__init__(self, pos.line, pos.col)

    @property
    def mode(self):
        return self._mode

class VimState(object):
    def __init__(self):
        """
        This class caches some state information from Vim to better guess what
        editing tasks the user might have done in the last step.
        """
        self._poss = deque(maxlen=5)
        self._lvb = None

    def remember_position(self):
        self._poss.append(VimPosition())

    def remember_buffer(self, to):
        self._lvb = _vim.buf[to.start.line:to.end.line+1]
        self._lvb_len = len(_vim.buf)
        self.remember_position()

    @property
    def diff_in_buffer_length(self):
        return len(_vim.buf) - self._lvb_len

    @property
    def pos(self):
        return self._poss[-1]

    @property
    def ppos(self):
        return self._poss[-2]

    @property
    def remembered_buffer(self):
        return self._lvb[:]
