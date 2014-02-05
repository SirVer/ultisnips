#!/usr/bin/env python
# encoding: utf-8

from UltiSnips.compatibility import as_unicode, byte2col
import UltiSnips._vim as _vim

class VisualContentPreserver(object):
    def __init__(self):
        """Saves the current visual selection and the selection mode it was
        done in (e.g. line selection, block selection or regular selection.)"""
        self.reset()

    def reset(self):
        self._mode = ""
        self._text = as_unicode("")

    def conserve(self):
        sl, sbyte = map(int, (_vim.eval("""line("'<")"""), _vim.eval("""col("'<")""")))
        el, ebyte = map(int, (_vim.eval("""line("'>")"""), _vim.eval("""col("'>")""")))
        sc = byte2col(sl, sbyte - 1)
        ec = byte2col(el, ebyte - 1)
        self._mode = _vim.eval("visualmode()")

        def _vim_line_with_eol(ln):
            return _vim.buf[ln] + '\n'

        if sl == el:
            text = _vim_line_with_eol(sl-1)[sc:ec+1]
        else:
            text = _vim_line_with_eol(sl-1)[sc:]
            for cl in range(sl,el-1):
                text += _vim_line_with_eol(cl)
            text += _vim_line_with_eol(el-1)[:ec+1]
        self._text = text

    @property
    def text(self):
        return self._text

    @property
    def mode(self):
        return self._mode
