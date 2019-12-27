#!/usr/bin/env python
# encoding: utf-8

"""This file contains compatibility code to stay compatible with as many python
versions as possible."""

import vim


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


def col2byte(line, col):
    """Convert a valid column index into a byte index inside of vims
    buffer."""
    # We pad the line so that selecting the +1 st column still works.
    pre_chars = (vim.current.buffer[line - 1] + "  ")[:col]
    return len(_vim_enc(pre_chars))


def byte2col(line, nbyte):
    """Convert a column into a byteidx suitable for a mark or cursor
    position inside of vim."""
    line = vim.current.buffer[line - 1]
    raw_bytes = _vim_enc(line)[:nbyte]
    return len(_vim_dec(raw_bytes))
