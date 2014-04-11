#!/usr/bin/env python
# encoding: utf-8

"""
This file contains compatibility code to stay compatible with
as many python versions as possible.
"""

import sys

import vim  # pylint:disable=import-error

if sys.version_info >= (3, 0):
    def _vim_dec(string):
        """Decode 'string' using &encoding."""
        # We don't have the luxury here of failing, everything
        # falls apart if we don't return a bytearray from the
        # passed in string
        return string.decode(vim.eval("&encoding"), "replace")

    def _vim_enc(bytearray):
        """Encode 'string' using &encoding."""
        # We don't have the luxury here of failing, everything
        # falls apart if we don't return a string from the passed
        # in bytearray
        return bytearray.encode(vim.eval("&encoding"), "replace")

    def open_ascii_file(filename, mode):
        """Opens a file in "r" mode."""
        return open(filename, mode, encoding="utf-8")

    def col2byte(line, col):
        """
        Convert a valid column index into a byte index inside
        of vims buffer.
        """
        # We pad the line so that selecting the +1 st column still works.
        pre_chars = (vim.current.buffer[line-1] + "  ")[:col]
        return len(_vim_enc(pre_chars))

    def byte2col(line, nbyte):
        """
        Convert a column into a byteidx suitable for a mark or cursor
        position inside of vim
        """
        line = vim.current.buffer[line-1]
        raw_bytes = _vim_enc(line)[:nbyte]
        return len(_vim_dec(raw_bytes))

    def as_unicode(string):
        """Return 'string' as unicode instance."""
        if isinstance(string, bytes):
            return _vim_dec(string)
        return str(string)

    def as_vimencoding(string):
        """Return 'string' as Vim internal encoding."""
        return string
else:
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    def _vim_dec(string):
        """Decode 'string' using &encoding."""
        try:
            return string.decode(vim.eval("&encoding"))
        except UnicodeDecodeError:
            # At least we tried. There might be some problems down the road now
            return string

    def _vim_enc(string):
        """Encode 'string' using &encoding."""
        try:
            return string.encode(vim.eval("&encoding"))
        except UnicodeEncodeError:
            return string

    def open_ascii_file(filename, mode):
        """Opens a file in "r" mode."""
        return open(filename, mode)

    def col2byte(line, col):
        """
        Convert a valid column index into a byte index inside
        of vims buffer.
        """
        # We pad the line so that selecting the +1 st column still works.
        pre_chars = _vim_dec(vim.current.buffer[line-1] + "  ")[:col]
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

    def as_unicode(string):
        """Return 'string' as unicode instance."""
        if isinstance(string, str):
            return _vim_dec(string)
        return unicode(string)

    def as_vimencoding(string):
        """Return 'string' as unicode instance."""
        return _vim_enc(string)
