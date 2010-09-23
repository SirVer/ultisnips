#!/usr/bin/env python
# encoding: utf-8

import vim
from UltiSnips.Geometry import Position

__all__ = [ "TextBuffer", "VimBuffer" ]

class Buffer(object):
    def _replace(self, start, end, content, first_line, last_line):

        text = content[:]
        if len(text) == 1:
            arr = [ first_line + text[0] + last_line ]
            new_end = start + Position(0,len(text[0]))
        else:
            arr = [ first_line + text[0] ] + \
                    text[1:-1] + \
                    [ text[-1] + last_line ]
            new_end = Position(start.line + len(text)-1, len(text[-1]))

        self[start.line:end.line+1] = arr

        return new_end

class TextBuffer(Buffer):
    def __init__(self, textblock):
        # We do not use splitlines() here because it handles cases like 'text\n'
        # differently than we want it here
        self._lines = textblock.replace('\r','').split('\n')

    def calc_end(self, start):
        text = self._lines[:]
        if len(text) == 1:
            new_end = start + Position(0,len(text[0]))
        else:
            new_end = Position(start.line + len(text)-1, len(text[-1]))
        return new_end

    def replace_text( self, start, end, content ):
        first_line = self[start.line][:start.col]
        last_line = self[end.line][end.col:]
        return self._replace( start, end, content, first_line, last_line)

    def __getitem__(self, a):
        return self._lines.__getitem__(a)
    def __setitem__(self, a, b):
        return self._lines.__setitem__(a,b)
    def __repr__(self):
        return repr('\n'.join(self._lines))
    def __str__(self):
        return '\n'.join(self._lines)

class VimBuffer(Buffer):
    def __init__(self, before, after):
        self._bf = before
        self._af = after
    def __getitem__(self, a):
        return vim.current.buffer[a]
    def __setitem__(self, a, b):
        if isinstance(a,slice):
            vim.current.buffer[a.start:a.stop] = b
        else:
            vim.current.buffer[a] = b

        # Open any folds this might have created
        vim.current.window.cursor = a.start + 1, 0
        vim.command("normal zv")

    def __repr__(self):
        return "VimBuffer()"

    def replace_lines( self, fline, eline, content ):
        start = Position(fline,0 )
        end = Position(eline, 100000)
        return self._replace( start, end, content, self._bf, self._af)


