#!/usr/bin/env python
# encoding: utf-8

import vim
from UltiSnips.Geometry import Position
from UltiSnips.Compatibility import make_suitable_for_vim, as_unicode

__all__ = [ "TextBuffer" ]

class TextBuffer(object):
    def __init__(self, textblock):
        # We do not use splitlines() here because it handles cases like 'text\n'
        # differently than we want it here
        self._lines = [ as_unicode(l) for l in textblock.replace('\r','').split('\n') ]

    def calc_end(self, start):
        text = self._lines[:]
        if len(text) == 1:
            new_end = start + Position(0,len(text[0]))
        else:
            new_end = Position(start.line + len(text)-1, len(text[-1]))
        return new_end

    def to_vim(self, start, end): # TODO: better take a span
        buf = vim.current.buffer

        # Open any folds this might have created
        vim.current.window.cursor = start.line + 1, start.col
        vim.command("normal zv")

        new_end = self.calc_end(start)

        before = as_unicode(buf[start.line])[:start.col]
        after = as_unicode(buf[end.line])[end.col:]
        lines = []
        if len(self._lines):
            lines.append(before + self._lines[0])
            lines.extend(self._lines[1:])
            lines[-1] += after
        buf[start.line:end.line + 1] = make_suitable_for_vim(lines)

        return new_end

    def __getitem__(self, a):
        try:
            s, e = a.start, a.end
            if s.line == e.line:
                return self._lines[s.line][s.col:e.col]
            else:
                return ('\n'.join(
                    [self._lines[s.line][s.col:]] +
                    self._lines[s.line+1:e.line] +
                    [self._lines[e.line][:e.col]]
                ))
        except AttributeError:
            return self._lines.__getitem__(a) # TODO: is this ever used?
    def __setitem__(self, a, b): # TODO: no longer needed?
        return self._lines.__setitem__(a,b)
    def __repr__(self):
        return repr('\n'.join(self._lines))
    def __str__(self):
        return '\n'.join(self._lines)
