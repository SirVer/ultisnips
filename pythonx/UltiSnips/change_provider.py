#!/usr/bin/env python3

"""Change providers that detect buffer modifications and produce edit commands.

Edit commands are tuples of ("I"|"D", line, col, text) where:
- "I" = insertion at (line, col) of text
- "D" = deletion at (line, col) of text
- text is either a string without newlines, or exactly "\\n"
- line numbers are 0-indexed absolute buffer positions
"""

import vim

from UltiSnips.diff import diff, guess_edit


def _guess_edit_with_trimming(snippet_start, old_lines, new_lines, vstate):
    """Run guess_edit with cursor-based line trimming, falling back to diff.

    This is the same logic that was previously inline in _cursor_moved().
    """
    lt_span = [0, len(old_lines)]
    ct_span = [0, len(new_lines)]
    initial_line = snippet_start
    pos = vstate.pos
    ppos = vstate.ppos

    if old_lines and new_lines:
        while (
            lt_span[0] < lt_span[1]
            and ct_span[0] < ct_span[1]
            and old_lines[lt_span[1] - 1] == new_lines[ct_span[1] - 1]
            and ppos.line < initial_line + lt_span[1] - 1
            and pos.line < initial_line + ct_span[1] - 1
        ):
            ct_span[1] -= 1
            lt_span[1] -= 1
        while (
            lt_span[0] < lt_span[1]
            and ct_span[0] < ct_span[1]
            and old_lines[lt_span[0]] == new_lines[ct_span[0]]
            and ppos.line >= initial_line
            and pos.line >= initial_line
        ):
            ct_span[0] += 1
            lt_span[0] += 1
            initial_line += 1
    ct_span[0] = max(0, ct_span[0] - 1)
    lt_span[0] = max(0, lt_span[0] - 1)
    initial_line = max(snippet_start, initial_line - 1)

    lt = old_lines[lt_span[0] : lt_span[1]]
    ct = new_lines[ct_span[0] : ct_span[1]]

    rv, es = guess_edit(initial_line, lt, ct, vstate)
    if not rv:
        es = diff("\n".join(lt), "\n".join(ct), initial_line)
    return es


def _consume_via_buffer_comparison(buf, snippet, vstate):
    """Detect edits by comparing remembered buffer with current state."""
    old_lines = vstate.remembered_buffer
    snippet_start = snippet.start.line
    new_end = snippet.end.line + (len(buf) - vstate.remembered_buffer_length)
    new_lines = buf[snippet_start : new_end + 1]
    return _guess_edit_with_trimming(snippet_start, old_lines, new_lines, vstate)


class VimChangeProvider:
    """Uses listener_add() as a reliable change signal for Vim.

    listener_add() fires for ALL buffer modifications regardless of mode.
    When a change is detected, we compare buffer snapshots and run
    guess_edit/diff to produce edit commands.
    """

    def __init__(self):
        self._attached = False

    def attach(self, bufnr):
        vim.command(f"call UltiSnips#listener#Attach({bufnr})")
        self._attached = True

    def detach(self):
        if self._attached:
            vim.command("call UltiSnips#listener#Detach()")
            self._attached = False

    def suppress(self):
        vim.command("let g:_ultisnips_listener_suppressed = 1")

    def unsuppress(self):
        vim.command("let g:_ultisnips_listener_suppressed = 0")

    def reset(self):
        vim.command("call UltiSnips#listener#Flush()")
        vim.command("let g:_ultisnips_listener_changes = []")

    def consume_edits(self, buf, snippet, vstate):
        vim.command("call UltiSnips#listener#Flush()")
        raw = vim.eval("g:_ultisnips_listener_changes")
        vim.command("let g:_ultisnips_listener_changes = []")
        if not raw:
            return None
        return _consume_via_buffer_comparison(buf, snippet, vstate)


class NvimChangeProvider:
    """Uses on_bytes as a reliable change signal for Neovim.

    nvim_buf_attach with on_bytes fires for ALL buffer modifications
    regardless of mode.  We use it as a change signal and compare buffer
    snapshots to produce edit commands — the same approach as the Vim
    provider.
    """

    def attach(self, bufnr):
        vim.command(f"lua require('ultisnips.on_bytes').attach({bufnr})")

    def detach(self):
        vim.command("lua require('ultisnips.on_bytes').detach()")

    def suppress(self):
        vim.command("lua require('ultisnips.on_bytes').suppress()")

    def unsuppress(self):
        vim.command("lua require('ultisnips.on_bytes').unsuppress()")

    def reset(self):
        vim.command("lua require('ultisnips.on_bytes').reset()")

    def consume_edits(self, buf, snippet, vstate):
        return _consume_via_buffer_comparison(buf, snippet, vstate)
