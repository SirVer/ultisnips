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

    def col2byte(line, col):
        """
        Convert a valid column index into a byte index inside
        of vims buffer.
        """
        pre_chars = vim.current.buffer[line-1][:col]
        return len(pre_chars.encode(vim.eval("&encoding")))

    def byte2col(line, nbyte):
        """
        Convert a column into a byteidx suitable for a mark or cursor
        position inside of vim
        """
        line = vim.current.buffer[line-1]
        vc = vim.eval("&encoding")
        raw_bytes = line.encode(vc)[:nbyte]
        return len(raw_bytes.decode(vc))

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

    def col2byte(line, col):
        """
        Convert a valid column index into a byte index inside
        of vims buffer.
        """
        vc = vim.eval("&encoding")
        pre_chars = vim.current.buffer[line-1].decode(vc)[:col]
        return len(pre_chars.encode(vc))

    def byte2col(line, nbyte):
        """
        Convert a column into a byteidx suitable for a mark or cursor
        position inside of vim
        """
        line = vim.current.buffer[line-1]
        if nbyte >= len(line): # This is beyond end of line
            return nbyte
        return len(line[:nbyte].decode(vim.eval("&encoding")))

    def as_unicode(s):
        if isinstance(s, str):
            vc = vim.eval("&encoding")
            return s.decode(vc)
        return unicode(s)

    def as_vimencoding(s):
        vc = vim.eval("&encoding")
        return s.encode(vc)

