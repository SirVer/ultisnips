#!/usr/bin/env python3

"""Change providers that detect buffer modifications and produce edit commands.

Edit commands are tuples of ("I"|"D", line, col, text) where:
- "I" = insertion at (line, col) of text
- "D" = deletion at (line, col) of text
- text is either a string without newlines, or exactly "\\n"
- line numbers are 0-indexed absolute buffer positions
"""

import vim

from UltiSnips.diff import diff


def _byte_to_char_col(line, byte_col):
    """Convert UTF-8 byte offset within a line to character offset."""
    if byte_col == 0:
        return 0
    encoded = line.encode("utf-8")
    if byte_col >= len(encoded):
        return len(line)
    return len(encoded[:byte_col].decode("utf-8", errors="replace"))


def _on_bytes_to_edits(event, old_lines, new_buf, snippet_start):
    """Translate one on_bytes event to edit commands.

    event: (start_row, start_col, old_end_row, old_end_col, new_end_row, new_end_col)
        Note: column values are UTF-8 BYTE offsets (Neovim convention).
    old_lines: remembered buffer slice (list of strings, snippet region)
    new_buf: current full buffer (for reading inserted text)
    snippet_start: absolute line number of snippet start

    Returns list of edit commands using CHARACTER columns (UltiSnips
    convention), or None if the event extends beyond available data
    (caller should fall back to detect_edits/diff).
    """
    start_row, start_col_b, old_end_row, old_end_col_b, new_end_row, new_end_col_b = (
        event
    )
    rel_row = start_row - snippet_start

    # Bounds checks: change must be within the snippet region we know about
    if rel_row < 0 or rel_row >= len(old_lines):
        return None
    if old_end_row > 0 and rel_row + old_end_row >= len(old_lines):
        return None
    if new_end_row > 0 and start_row + new_end_row >= len(new_buf):
        return None

    cmds = []
    # The line at start_row exists in both old and new (change starts AT this
    # row, not above), so byte→char conversion at start_col_b yields the same
    # character position in both.
    start_col = _byte_to_char_col(old_lines[rel_row], start_col_b)

    # --- Deletion ---
    if old_end_row == 0 and old_end_col_b > 0:
        end_col = _byte_to_char_col(old_lines[rel_row], start_col_b + old_end_col_b)
        deleted = old_lines[rel_row][start_col:end_col]
        cmds.append(("D", start_row, start_col, deleted))
    elif old_end_row > 0:
        # Multi-line deletion — all at (start_row, start_col)
        rest = old_lines[rel_row][start_col:]
        if rest:
            cmds.append(("D", start_row, start_col, rest))
        cmds.append(("D", start_row, start_col, "\n"))
        for i in range(1, old_end_row):
            content = old_lines[rel_row + i]
            if content:
                cmds.append(("D", start_row, start_col, content))
            cmds.append(("D", start_row, start_col, "\n"))
        last_line = old_lines[rel_row + old_end_row]
        last_end_col = _byte_to_char_col(last_line, old_end_col_b)
        last = last_line[:last_end_col]
        if last:
            cmds.append(("D", start_row, start_col, last))

    # --- Insertion ---
    if new_end_row == 0 and new_end_col_b > 0:
        end_col = _byte_to_char_col(new_buf[start_row], start_col_b + new_end_col_b)
        inserted = new_buf[start_row][start_col:end_col]
        cmds.append(("I", start_row, start_col, inserted))
    elif new_end_row > 0:
        first = new_buf[start_row][start_col:]
        if first:
            cmds.append(("I", start_row, start_col, first))
        cmds.append(("I", start_row, start_col + len(first), "\n"))
        for i in range(1, new_end_row):
            content = new_buf[start_row + i]
            if content:
                cmds.append(("I", start_row + i, 0, content))
            cmds.append(("I", start_row + i, len(content), "\n"))
        last_new_line = new_buf[start_row + new_end_row]
        last_end_col = _byte_to_char_col(last_new_line, new_end_col_b)
        last_text = last_new_line[:last_end_col]
        if last_text:
            cmds.append(("I", start_row + new_end_row, 0, last_text))

    return cmds


def _suffix_match(old_line, new_line, prefix):
    """Largest suffix length where old_line and new_line match, given prefix already matches."""
    suffix = 0
    max_suffix = min(len(old_line) - prefix, len(new_line) - prefix)
    while (
        suffix < max_suffix
        and old_line[len(old_line) - 1 - suffix] == new_line[len(new_line) - 1 - suffix]
    ):
        suffix += 1
    return suffix


def _common_prefix_suffix(old_line, new_line):
    """Greedy common prefix and (then) suffix between two strings."""
    prefix = 0
    max_prefix = min(len(old_line), len(new_line))
    while prefix < max_prefix and old_line[prefix] == new_line[prefix]:
        prefix += 1
    suffix = _suffix_match(old_line, new_line, prefix)
    return prefix, suffix


def detect_edits(old_lines, new_lines, start_line, cursor_line, cursor_col):
    """Produce edit commands transforming old_lines into new_lines.

    Returns list of edit commands, or None if detection fails.
    """
    if old_lines == new_lines:
        return []

    n_old = len(old_lines)
    n_new = len(new_lines)
    cursor_rel = cursor_line - start_line

    if n_old == n_new:
        # Same line count — per-line character diff
        cmds = []
        for i in range(n_old):
            if old_lines[i] == new_lines[i]:
                continue
            old_line = old_lines[i]
            new_line = new_lines[i]
            prefix, suffix = _common_prefix_suffix(old_line, new_line)
            # Cursor disambiguation: on the cursor's line, constrain prefix
            # to be no greater than the position where the edit actually
            # happened. After reducing prefix, suffix can grow naturally.
            if i == cursor_rel:
                del_len = len(old_line) - prefix - suffix
                ins_len = len(new_line) - prefix - suffix
                max_prefix = None
                if ins_len > del_len:
                    # Insertion: cursor ends after inserted text
                    max_prefix = cursor_col - (ins_len - del_len)
                elif del_len > ins_len:
                    # Deletion: cursor at deletion point
                    max_prefix = cursor_col
                if max_prefix is not None and prefix > max_prefix:
                    prefix = max(0, max_prefix)
                    suffix = _suffix_match(old_line, new_line, prefix)

            abs_line = start_line + i
            deleted = old_line[prefix : len(old_line) - suffix if suffix else None]
            inserted = new_line[prefix : len(new_line) - suffix if suffix else None]
            if deleted:
                cmds.append(("D", abs_line, prefix, deleted))
            if inserted:
                cmds.append(("I", abs_line, prefix, inserted))
        return cmds

    # Trim matching prefix lines (cursor-aware)
    top = 0
    while (
        top < min(n_old, n_new)
        and old_lines[top] == new_lines[top]
        and top < cursor_rel
    ):
        top += 1

    # Trim matching suffix lines (cursor-aware)
    bot_old = n_old
    bot_new = n_new
    while (
        bot_old > top
        and bot_new > top
        and old_lines[bot_old - 1] == new_lines[bot_new - 1]
        and (bot_new - 1) > cursor_rel
    ):
        bot_old -= 1
        bot_new -= 1

    rem_old = old_lines[top:bot_old]
    rem_new = new_lines[top:bot_new]
    base_line = start_line + top

    if n_old > n_new:
        # Lines removed
        if not rem_new and rem_old:
            # Pure line deletion
            cmds = []
            for line_content in rem_old:
                cmds.append(("D", base_line, 0, line_content))
                cmds.append(("D", base_line, 0, "\n"))
            # Last deleted line: remove the \n only if it merges with next line
            # Actually for pure deletion of full lines, all get \n
            return cmds

        if len(rem_new) == 1 and len(rem_old) >= 1:
            # Lines removed with possible content change on remaining line
            # Try: content of rem_new[0] is the merge of first and last rem_old
            # with middle lines fully deleted
            cmds = []
            # Delete from line base_line: all middle/extra lines
            # Work out if rem_new[0] = prefix_of_first + suffix_of_last
            first_old = rem_old[0]
            last_old = rem_old[-1]

            # Find how much of first_old is kept (prefix)
            p = 0
            max_p = min(len(first_old), len(rem_new[0]))
            while p < max_p and first_old[p] == rem_new[0][p]:
                p += 1

            # Find how much of last_old is kept (suffix)
            s = 0
            max_s = min(len(last_old), len(rem_new[0]) - p)
            while (
                s < max_s
                and last_old[len(last_old) - 1 - s]
                == rem_new[0][len(rem_new[0]) - 1 - s]
            ):
                s += 1

            # Check if the remaining new content is fully explained
            kept_prefix = first_old[:p]
            kept_suffix = last_old[len(last_old) - s :] if s else ""
            middle_new = rem_new[0][p : len(rem_new[0]) - s if s else None]

            if kept_prefix + middle_new + kept_suffix == rem_new[0] and not middle_new:
                # Delete rest of first line, \n, full middle lines, beginning of last
                deleted_from_first = first_old[p:]
                if deleted_from_first:
                    cmds.append(("D", base_line, p, deleted_from_first))
                cmds.append(("D", base_line, p, "\n"))
                for i in range(1, len(rem_old) - 1):
                    if rem_old[i]:
                        cmds.append(("D", base_line, p, rem_old[i]))
                    cmds.append(("D", base_line, p, "\n"))
                deleted_from_last = last_old[: len(last_old) - s] if s else last_old
                if deleted_from_last:
                    cmds.append(("D", base_line, p, deleted_from_last))
                return cmds

        return None

    if n_new > n_old:
        # Lines added
        added = n_new - n_old

        if len(rem_old) == 1 and len(rem_new) == added + 1:
            # Line was split (Enter key or paste)
            old_line = rem_old[0]

            if added == 1:
                # Simple Enter: old_line split into rem_new[0] and rem_new[1]
                # Find split point: rem_new[0] is prefix, rem_new[1] ends with suffix
                if rem_new[0] + rem_new[1] == old_line:
                    # Clean split, no indent change
                    split_col = len(rem_new[0])
                    return [("I", base_line, split_col, "\n")]

                # Split with content change (e.g., auto-indent)
                # rem_new[0] should be a prefix of old_line (possibly trimmed)
                # Find what was deleted from end of first line
                p = 0
                max_p = min(len(old_line), len(rem_new[0]))
                while p < max_p and old_line[p] == rem_new[0][p]:
                    p += 1

                s = 0
                max_s = min(len(old_line) - p, len(rem_new[1]))
                while (
                    s < max_s
                    and old_line[len(old_line) - 1 - s]
                    == rem_new[1][len(rem_new[1]) - 1 - s]
                ):
                    s += 1

                # The split happened at position p in old_line
                # After split: first part is rem_new[0], second part is rem_new[1]
                cmds = []
                deleted_tail = old_line[p : len(old_line) - s if s else None]
                new_second_part = rem_new[1][: len(rem_new[1]) - s if s else None]

                # Insert newline at split point
                if deleted_tail:
                    cmds.append(("D", base_line, p, deleted_tail))
                extra_on_first = rem_new[0][p:]
                if extra_on_first:
                    cmds.append(("I", base_line, p, extra_on_first))
                cmds.append(("I", base_line, len(rem_new[0]), "\n"))
                if new_second_part:
                    cmds.append(("I", base_line + 1, 0, new_second_part))
                return cmds

        return None

    return None


def _listener_to_edits(
    event, old_lines, new_buf, snippet_start, cursor_line, cursor_col
):
    """Translate a single Vim listener_add event to edit commands.

    event: dict with 'lnum' (1-indexed first changed line), 'end' (1-indexed
           line past last original changed line), 'added' (lines added, can
           be negative).
    old_lines: remembered buffer slice (snippet region).
    new_buf: current full buffer.
    snippet_start: absolute line number of snippet start.

    Uses the listener metadata to scope detect_edits to just the affected
    lines, improving disambiguation for cases with identical lines.
    """
    lnum = int(event["lnum"])  # 1-indexed
    end = int(event["end"])  # 1-indexed, exclusive
    added = int(event["added"])

    start_0 = lnum - 1  # 0-indexed absolute line
    old_count = end - lnum
    new_count = old_count + added

    rel_start = start_0 - snippet_start
    if rel_start < 0 or rel_start + old_count > len(old_lines):
        return None  # Change outside snippet region

    old_region = old_lines[rel_start : rel_start + old_count]
    new_region = list(new_buf[start_0 : start_0 + new_count])

    return detect_edits(old_region, new_region, start_0, cursor_line, cursor_col)


class VimChangeProvider:
    """Uses listener_add() as a reliable change signal for Vim.

    listener_add() fires for ALL buffer modifications regardless of mode.
    When a change is detected, we compare buffer snapshots and run
    detect_edits/diff to produce edit commands.
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

        old_lines = vstate.remembered_buffer
        snippet_start = snippet.start.line
        pos = buf.cursor

        if len(raw) == 1:
            # Single event: use listener metadata to scope comparison
            es = _listener_to_edits(
                raw[0], old_lines, buf, snippet_start, pos.line, pos.col
            )
            if es is not None:
                return es or None

        # Multiple events or scoped detection failed: full snippet comparison
        new_end = snippet.end.line + (len(buf) - vstate.remembered_buffer_length)
        new_lines = buf[snippet_start : new_end + 1]

        es = detect_edits(old_lines, new_lines, snippet_start, pos.line, pos.col)
        if es is not None:
            return es or None
        return diff("\n".join(old_lines), "\n".join(new_lines), snippet_start)


class NvimChangeProvider:
    """Uses on_bytes for deterministic edit detection in Neovim.

    For single on_bytes events, translates the exact byte coordinates
    directly to edit commands. For multiple events between CursorMoved
    calls, falls back to buffer comparison via detect_edits/diff.
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
        raw = vim.eval("g:_ultisnips_nvim_changes")
        vim.command("lua require('ultisnips.on_bytes').reset()")
        if not raw:
            return None

        old_lines = vstate.remembered_buffer
        snippet_start = snippet.start.line

        if len(raw) == 1:
            event = tuple(int(x) for x in raw[0])
            es = _on_bytes_to_edits(event, old_lines, buf, snippet_start)
            if es is not None:
                return es or None

        new_end = snippet.end.line + (len(buf) - vstate.remembered_buffer_length)
        new_lines = buf[snippet_start : new_end + 1]
        pos = buf.cursor

        es = detect_edits(old_lines, new_lines, snippet_start, pos.line, pos.col)
        if es is not None:
            return es or None
        return diff("\n".join(old_lines), "\n".join(new_lines), snippet_start)
