#!/usr/bin/env python
# encoding: utf-8

"""
This file contains compatibility code to stay compatible with
as many python versions as possible.
"""

import sys

import vim

__all__ = ['as_unicode', 'compatible_exec', 'vim_cursor', 'set_vim_cursor']

def _vim_dec(s):
    try:
        return s.decode(vim.eval("&encoding"))
    except UnicodeDecodeError:
        # At least we tried. There might be some problems down the road now
        return s

def _vim_enc(s):
    try:
        return s.encode(vim.eval("&encoding"))
    except UnicodeEncodeError:
        return s

if sys.version_info >= (3,0):
    from UltiSnips.compatibility_py3 import *

    def col2byte(line, col):
        """
        Convert a valid column index into a byte index inside
        of vims buffer.
        """
        pre_chars = vim.current.buffer[line-1][:col]
        return len(_vim_enc(pre_chars))

    def byte2col(line, nbyte):
        """
        Convert a column into a byteidx suitable for a mark or cursor
        position inside of vim
        """
        line = vim.current.buffer[line-1]
        raw_bytes = _vim_enc(line)[:nbyte]
        return len(_vim_dec(raw_bytes))

    def as_unicode(s):
        if isinstance(s, bytes):
            return _vim_dec(s)
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
        pre_chars = _vim_dec(vim.current.buffer[line-1])[:col]
        return len(_vim_enc(pre_chars))

    def byte2col(line, nbyte):
        """
        Convert a column into a byteidx suitable for a mark or cursor
        position inside of vim
        """
        line = vim.current.buffer[line-1]
        if nbyte >= len(line): # This is beyond end of line
            return nbyte
        return len(_vim_dec(line[:nbyte]))

    def as_unicode(s):
        if isinstance(s, str):
            return _vim_dec(s)
        return unicode(s)

    def as_vimencoding(s):
        return _vim_enc(s)

