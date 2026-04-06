#!/usr/bin/env python3

"""Change providers that detect buffer modifications and produce edit commands.

Edit commands are tuples of ("I"|"D", line, col, text) where:
- "I" = insertion at (line, col) of text
- "D" = deletion at (line, col) of text
- text is either a string without newlines, or exactly "\\n"
- line numbers are 0-indexed absolute buffer positions
"""

from abc import ABC, abstractmethod

import vim

from UltiSnips.diff import diff, guess_edit


class ChangeProvider(ABC):
    """Abstract base for buffer change detection."""

    @abstractmethod
    def attach(self, bufnr):
        """Start listening for changes on the given buffer."""

    @abstractmethod
    def detach(self):
        """Stop listening."""

    @abstractmethod
    def suppress(self):
        """Temporarily suppress change tracking (during proxy buffer ops)."""

    @abstractmethod
    def unsuppress(self):
        """Resume change tracking after suppression."""

    @abstractmethod
    def reset(self):
        """Discard all accumulated changes. Call after remember_buffer()."""

    @abstractmethod
    def consume_edits(self, buf, snippet, vstate):
        """Return accumulated edit commands and clear internal state.

        Returns a list of edit command tuples, or None if no changes detected.
        """


def _line_diff(old_line, new_line, line_nr, cursor_col=None):
    """Produce edit commands for a single changed line.

    Finds the differing region between old_line and new_line and emits a
    delete (if any chars were removed) followed by an insert (if any chars
    were added).

    When cursor_col is given, it constrains the prefix length so that the
    edit position doesn't overshoot the cursor.  This is critical for
    ambiguous cases like "ab" -> "abb" where the cursor position
    disambiguates whether "b" was inserted at col 1 or col 2.
    """
    # Find common prefix.
    prefix = 0
    limit = min(len(old_line), len(new_line))
    while prefix < limit and old_line[prefix] == new_line[prefix]:
        prefix += 1

    # If cursor info is available, don't let prefix overshoot the cursor.
    # The edit must have happened at or before the cursor position.
    if cursor_col is not None:
        if len(new_line) > len(old_line):
            # Insertion: cursor is now AFTER the inserted text.
            insert_len = len(new_line) - len(old_line)
            max_prefix = max(0, cursor_col - insert_len)
            prefix = min(prefix, max_prefix)
        elif len(new_line) < len(old_line):
            # Deletion: cursor is at the deletion point.
            prefix = min(prefix, cursor_col)

    # Find common suffix (not overlapping with prefix).
    suffix = 0
    while (
        suffix < (len(old_line) - prefix)
        and suffix < (len(new_line) - prefix)
        and old_line[-(suffix + 1)] == new_line[-(suffix + 1)]
    ):
        suffix += 1

    cmds = []
    deleted = old_line[prefix : len(old_line) - suffix] if suffix else old_line[prefix:]
    inserted = (
        new_line[prefix : len(new_line) - suffix] if suffix else new_line[prefix:]
    )

    if deleted:
        cmds.append(("D", line_nr, prefix, deleted))
    if inserted:
        cmds.append(("I", line_nr, prefix, inserted))
    return cmds


def _edits_for_line_range(
    old_lines, new_lines, start_line, cursor_line=None, cursor_col=None
):
    """Produce edit commands that transform old_lines into new_lines.

    Handles three cases:
    1. Same number of lines: within-line diffs using cursor position
    2. Lines deleted: content-first deletion commands (preserves _do_edit
       semantics for tabstop killing)
    3. Lines added: falls back to guess_edit/diff since cursor position is
       needed to determine the split point

    All produced edit commands follow the conventions expected by _do_edit.
    """
    if old_lines == new_lines:
        return []

    # Trim matching lines from front and back, but never trim past the
    # cursor line — with mirrors, multiple lines can be identical and
    # trimming the cursor's line would misattribute the edit.
    cursor_idx = (cursor_line - start_line) if cursor_line is not None else None
    front = 0
    limit = min(len(old_lines), len(new_lines))
    while (
        front < limit
        and old_lines[front] == new_lines[front]
        and (cursor_idx is None or front < cursor_idx)
    ):
        front += 1
    back = 0
    while (
        back < (len(old_lines) - front)
        and back < (len(new_lines) - front)
        and old_lines[-(back + 1)] == new_lines[-(back + 1)]
        and (cursor_idx is None or (len(new_lines) - back - 1) > cursor_idx)
    ):
        back += 1

    old_core = old_lines[front : len(old_lines) - back] if back else old_lines[front:]
    new_core = new_lines[front : len(new_lines) - back] if back else new_lines[front:]
    line_nr = start_line + front

    if len(old_core) == len(new_core):
        # Case 1: Same number of lines -- within-line diffs.
        cmds = []
        for i in range(len(old_core)):
            if old_core[i] != new_core[i]:
                col = cursor_col if (cursor_line == line_nr + i) else None
                cmds.extend(_line_diff(old_core[i], new_core[i], line_nr + i, col))
        return cmds

    if len(old_core) > len(new_core):
        # Case 2: Lines were deleted.
        common = len(new_core)
        has_line_changes = any(old_core[i] != new_core[i] for i in range(common))
        if not has_line_changes:
            # Pure line deletion -- emit content-first deletion commands.
            cmds = []
            del_line = line_nr + common
            for i in range(common, len(old_core)):
                content = old_core[i]
                if content:
                    cmds.append(("D", del_line, 0, content))
                cmds.append(("D", del_line, 0, "\n"))
            return cmds

    # Line count changed with content modifications, or lines added.
    # Signal caller to use guess_edit (which uses cursor position to
    # anchor the edit correctly when mirrors make buffer regions identical).
    return None


class VimListenerChangeProvider(ChangeProvider):
    """Uses Vim's listener_add() for reliable, mode-independent change detection.

    listener_add() fires for ALL buffer modifications regardless of mode,
    macros, or external plugins.  It provides line-level granularity (which
    lines changed and how many were added/removed).  Character-level edits
    are derived by direct comparison of old vs new line content — no
    heuristic guessing or general-purpose diff algorithm needed.
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
        # Flush any buffered listener events.
        vim.command("call UltiSnips#listener#Flush()")

        raw = vim.eval("g:_ultisnips_listener_changes")
        vim.command("let g:_ultisnips_listener_changes = []")

        if not raw:
            return None

        old_lines = vstate.remembered_buffer
        snippet_start = snippet.start.line
        new_end_line = snippet.end.line + (len(buf) - vstate.remembered_buffer_length)
        new_lines = buf[snippet_start : new_end_line + 1]

        pos = buf.cursor
        es = _edits_for_line_range(
            old_lines, new_lines, snippet_start, pos.line, pos.col
        )
        if es is not None:
            return es or None

        # Line count changed: fall back to guess_edit which uses cursor
        # position to anchor the edit correctly when mirrors make multiple
        # buffer regions identical.
        rv, es = guess_edit(snippet_start, old_lines, new_lines, vstate)
        if not rv:
            lt = "\n".join(old_lines)
            ct = "\n".join(new_lines)
            es = diff(lt, ct, snippet_start)
        return es


class NvimOnBytesChangeProvider(ChangeProvider):
    """Uses Neovim's nvim_buf_attach with on_bytes as a change signal.

    on_bytes fires for ALL buffer modifications regardless of mode.  We use
    it purely as a "something changed" signal and then compare old vs new
    buffer state -- the same approach as VimListenerChangeProvider.  This
    avoids issues with accumulated multi-change coordinates and undo/redo.
    """

    def __init__(self):
        self._attached = False

    def attach(self, bufnr):
        vim.command(f"lua require('ultisnips.on_bytes').attach({bufnr})")
        self._attached = True

    def detach(self):
        if self._attached:
            vim.command("lua require('ultisnips.on_bytes').detach()")
            self._attached = False

    def suppress(self):
        vim.command("lua require('ultisnips.on_bytes').suppress()")

    def unsuppress(self):
        vim.command("lua require('ultisnips.on_bytes').unsuppress()")

    def reset(self):
        vim.command("lua require('ultisnips.on_bytes').reset()")

    def consume_edits(self, buf, snippet, vstate):
        raw = vim.eval("g:_ultisnips_nvim_changes")
        vim.command("let g:_ultisnips_nvim_changes = []")

        if not raw:
            return None

        # Use the same buffer-comparison approach as VimListenerChangeProvider.
        old_lines = vstate.remembered_buffer
        snippet_start = snippet.start.line
        new_end_line = snippet.end.line + (len(buf) - vstate.remembered_buffer_length)
        new_lines = buf[snippet_start : new_end_line + 1]

        pos = buf.cursor
        es = _edits_for_line_range(
            old_lines, new_lines, snippet_start, pos.line, pos.col
        )
        if es is not None:
            return es or None

        # Fall back to guess_edit for line-count changes.
        rv, es = guess_edit(snippet_start, old_lines, new_lines, vstate)
        if not rv:
            lt = "\n".join(old_lines)
            ct = "\n".join(new_lines)
            es = diff(lt, ct, snippet_start)
        return es
