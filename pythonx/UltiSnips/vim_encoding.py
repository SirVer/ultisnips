"""Helpers for converting between Python string indices and Vim byte offsets.

Vim uses byte offsets internally while Python uses character indices. These
differ for multi-byte characters (UTF-8).
"""

import vim


def _vim_enc(string):
    """Encode 'string' using Vim's &encoding."""
    return string.encode(vim.eval("&encoding"), "replace")


def _vim_dec(raw_bytes):
    """Decode 'raw_bytes' using Vim's &encoding."""
    return raw_bytes.decode(vim.eval("&encoding"), "replace")


def col2byte(line, col):
    """Convert a column index into a byte index inside Vim's buffer."""
    pre_chars = (vim.current.buffer[line - 1] + "  ")[:col]
    return len(_vim_enc(pre_chars))


def byte2col(line, nbyte):
    """Convert a byte index into a column index inside Vim's buffer."""
    raw_bytes = _vim_enc(vim.current.buffer[line - 1])[:nbyte]
    return len(_vim_dec(raw_bytes))
