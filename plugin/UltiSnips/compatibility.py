#!/usr/bin/env python
# encoding: utf-8

"""
This file contains compatibility code to stay compatible with
as many python versions as possible.
"""

import sys

import vim

__all__ = ['as_unicode', 'compatible_exec', 'vim_cursor', 'set_vim_cursor']

if sys.version_info >= (3,0):
    from UltiSnips.compatibility_py3 import *

    def set_vim_cursor(line, col):
        """Wrapper around vims access to window.cursor. It can't handle
        multibyte chars, we therefore have to compensate"""

        pre_chars = vim.current.buffer[line-1][:col]
        vc = vim.eval("&encoding")
        nbytes = len(pre_chars.encode(vc))

        vim.current.window.cursor = line, nbytes

    def vim_cursor():
        """Returns the character position (not the byte position) of the
        vim cursor"""

        line, nbyte = vim.current.window.cursor

        vc = vim.eval("&encoding")
        raw_bytes = vim.current.buffer[line-1].encode(vc)[:nbyte]

        col = len(raw_bytes.decode(vc))
        return line, col
    def as_unicode(s):
        if isinstance(s, bytes):
            vc = vim.eval("&encoding")
            return s.decode(vc)
        return str(s)

    def as_vimencoding(s):
        return s
else:
    from UltiSnips.compatibility_py2 import *

    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    def set_vim_cursor(line, col):
        """Wrapper around vims access to window.cursor. It can't handle
        multibyte chars, we therefore have to compensate"""

        vc = vim.eval("&encoding")
        pre_chars = vim.current.buffer[line-1].decode(vc)[:col]
        nbytes = len(pre_chars.encode(vc))

        vim.current.window.cursor = line, nbytes

    def vim_cursor():
        """Returns the character position (not the byte position) of the
        vim cursor"""

        line, nbyte = vim.current.window.cursor

        raw_bytes = vim.current.buffer[line-1][:nbyte]

        vc = vim.eval("&encoding")
        col = len(raw_bytes.decode(vc))
        return line, col

    def as_unicode(s):
        if isinstance(s, str):
            vc = vim.eval("&encoding")
            return s.decode(vc)
        return unicode(s)

    def as_vimencoding(s):
        vc = vim.eval("&encoding")
        return s.encode(vc)

