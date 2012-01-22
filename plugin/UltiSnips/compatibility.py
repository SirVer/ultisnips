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
        nbytes = len(pre_chars.encode("utf-8"))

        vim.current.window.cursor = line, nbytes

    def vim_cursor():
        """Returns the character position (not the byte position) of the
        vim cursor"""

        line, nbyte = vim.current.window.cursor

        raw_bytes = vim.current.buffer[line-1].encode("utf-8")[:nbyte]

        col = len(raw_bytes.decode("utf-8"))
        return line, col
    def as_unicode(s):
        if isinstance(s, bytes):
            return s.decode("utf-8")
        return str(s)

    def as_vimencoding(s):
        return s
else:
    from UltiSnips.compatibility_py2 import *

    def set_vim_cursor(line, col):
        """Wrapper around vims access to window.cursor. It can't handle
        multibyte chars, we therefore have to compensate"""

        pre_chars = vim.current.buffer[line-1].decode("utf-8")[:col]
        nbytes = len(pre_chars.encode("utf-8"))

        vim.current.window.cursor = line, nbytes

    def vim_cursor():
        """Returns the character position (not the byte position) of the
        vim cursor"""

        line, nbyte = vim.current.window.cursor

        raw_bytes = vim.current.buffer[line-1][:nbyte]

        col = len(raw_bytes.decode("utf-8"))
        return line, col

    def as_unicode(s):
        if isinstance(s, str):
            return s.decode("utf-8")
        return unicode(s)

    def as_vimencoding(s):
        return s.encode("utf-8")

