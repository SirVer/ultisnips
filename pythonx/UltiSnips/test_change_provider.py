#!/usr/bin/env python3

"""Tests for change_provider pure-Python helper functions.

Tests detect_edits and _on_bytes_to_edits as pure functions (no Vim dependency).
"""

import importlib.util
import os
import sys
import types
import unittest

# Load change_provider in isolation: it has `import vim` and
# `from UltiSnips.diff import diff` at module level, but the full
# UltiSnips package needs a live Vim runtime to import.  We temporarily
# install minimal stubs in sys.modules, load change_provider, then
# restore sys.modules so other test files (e.g. test_diff.py) see the
# real package.
_here = os.path.dirname(os.path.abspath(__file__))
_stub_keys = ["vim", "UltiSnips", "UltiSnips.diff", "UltiSnips.change_provider"]
_saved = {k: sys.modules.get(k) for k in _stub_keys}

sys.modules["vim"] = types.ModuleType("vim")

_pkg = types.ModuleType("UltiSnips")
_pkg.__path__ = [_here]
_pkg.__package__ = "UltiSnips"
sys.modules["UltiSnips"] = _pkg

# change_provider only uses diff() as a fallback, which these tests never
# exercise — the stub is enough for `from UltiSnips.diff import diff`.
_mock_diff = types.ModuleType("UltiSnips.diff")
_mock_diff.diff = None
sys.modules["UltiSnips.diff"] = _mock_diff

_spec = importlib.util.spec_from_file_location(
    "UltiSnips.change_provider", os.path.join(_here, "change_provider.py")
)
_cp = importlib.util.module_from_spec(_spec)
sys.modules["UltiSnips.change_provider"] = _cp
_spec.loader.exec_module(_cp)

_on_bytes_to_edits = _cp._on_bytes_to_edits
_listener_to_edits = _cp._listener_to_edits
detect_edits = _cp.detect_edits

# Restore sys.modules so other test files load the real UltiSnips package.
for k, v in _saved.items():
    if v is None:
        sys.modules.pop(k, None)
    else:
        sys.modules[k] = v


def _apply(old_lines, cmds, start_line=0):
    """Apply edit commands to old_lines, return resulting lines list."""
    buf = old_lines[:]
    for cmd in cmds:
        ctype, line, col, char = cmd
        line -= start_line
        if ctype == "D":
            if char != "\n":
                buf[line] = buf[line][:col] + buf[line][col + len(char) :]
            else:
                if line + 1 < len(buf):
                    buf[line] = buf[line] + buf[line + 1]
                    del buf[line + 1]
                else:
                    del buf[line]
        elif ctype == "I":
            buf[line] = buf[line][:col] + char + buf[line][col:]
        buf = "\n".join(buf).split("\n")
    return buf


class TestDetectEdits(unittest.TestCase):
    """Test detect_edits for common editing patterns."""

    def _check(self, old, new, start, cursor_line, cursor_col):
        """Run detect_edits and verify the result transforms old into new."""
        cmds = detect_edits(old, new, start, cursor_line, cursor_col)
        self.assertIsNotNone(cmds, "detect_edits returned None (gave up)")
        result = _apply(old, cmds, start)
        self.assertEqual(
            result, new, f"Commands {cmds} did not transform {old} to {new}"
        )
        return cmds

    def test_no_change(self):
        cmds = self._check(["hello"], ["hello"], 0, 0, 5)
        self.assertEqual(cmds, [])

    def test_single_char_insert(self):
        cmds = self._check(["hello"], ["helxlo"], 0, 0, 4)
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0][0], "I")

    def test_single_char_insert_at_end(self):
        cmds = self._check(["hello"], ["hellox"], 0, 0, 6)
        self.assertEqual(cmds, [("I", 0, 5, "x")])

    def test_single_char_delete_backspace(self):
        cmds = self._check(["hello"], ["helo"], 0, 0, 3)
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0][0], "D")

    def test_single_char_delete_x(self):
        # 'x' key at col 1: cursor stays at col 1, 'e' deleted
        cmds = self._check(["hello"], ["hllo"], 0, 0, 1)
        self.assertEqual(cmds, [("D", 0, 1, "e")])

    def test_multi_char_insert_completion(self):
        cmds = self._check(["hel"], ["hello"], 0, 0, 5)
        self.assertEqual(cmds, [("I", 0, 3, "lo")])

    def test_multi_char_delete(self):
        cmds = self._check(["hello"], ["ho"], 0, 0, 1)
        self.assertEqual(cmds, [("D", 0, 1, "ell")])

    def test_replace_on_same_line(self):
        cmds = self._check(["hello"], ["hXYZo"], 0, 0, 4)
        self.assertEqual(len(cmds), 2)  # D + I

    def test_ambiguous_insert_cursor_disambiguates(self):
        # "ab" -> "abb" — could be insert 'b' at pos 1 or pos 2
        # Cursor at col 2 means insert was at col 1 (before existing 'b')
        cmds = self._check(["ab"], ["abb"], 0, 0, 2)
        result = _apply(["ab"], cmds, 0)
        self.assertEqual(result, ["abb"])

    def test_with_nonzero_start_line(self):
        cmds = self._check(["hello"], ["helxlo"], 5, 5, 4)
        self.assertEqual(cmds[0][1], 5)  # line number should be absolute

    def test_insert_with_repeated_pattern_after(self):
        # Regression: inserting a space at col 5 in "hallo hallo hallo hallo"
        # The greedy prefix matches "hallo " (6 chars), then cursor disambiguation
        # must reduce prefix to 5 AND let suffix grow so the result is a clean
        # 1-char insertion, not a delete-and-insert.
        cmds = self._check(
            ["hallo hallo hallo hallo"], ["hallo  hallo hallo hallo"], 0, 0, 6
        )
        self.assertEqual(cmds, [("I", 0, 5, " ")])

    def test_insert_in_repeated_substring(self):
        # Insert "x" between two identical "abc" substrings: "abcabc" → "abcxabc"
        # Greedy prefix could match all 3 of "abc" before differing.
        cmds = self._check(["abcabc"], ["abcxabc"], 0, 0, 4)
        self.assertEqual(cmds, [("I", 0, 3, "x")])

    def test_line_deletion_dd(self):
        cmds = self._check(["a", "b", "c"], ["a", "c"], 0, 1, 0)
        self.assertIsNotNone(cmds)
        result = _apply(["a", "b", "c"], cmds, 0)
        self.assertEqual(result, ["a", "c"])

    def test_multi_line_deletion(self):
        cmds = self._check(["a", "b", "c", "d"], ["a", "d"], 0, 1, 0)
        self.assertIsNotNone(cmds)
        result = _apply(["a", "b", "c", "d"], cmds, 0)
        self.assertEqual(result, ["a", "d"])

    def test_enter_simple_split(self):
        cmds = self._check(["hello"], ["hel", "lo"], 0, 1, 0)
        self.assertIsNotNone(cmds)
        result = _apply(["hello"], cmds, 0)
        self.assertEqual(result, ["hel", "lo"])

    def test_enter_with_indent(self):
        cmds = self._check(["hello"], ["hel", "  lo"], 0, 1, 2)
        self.assertIsNotNone(cmds)
        result = _apply(["hello"], cmds, 0)
        self.assertEqual(result, ["hel", "  lo"])

    def test_multiple_lines_changed(self):
        # Two lines changed simultaneously (e.g., multi-cursor or mirror)
        cmds = self._check(["aaa", "bbb"], ["axa", "bxb"], 0, 0, 2)
        self.assertIsNotNone(cmds)
        result = _apply(["aaa", "bbb"], cmds, 0)
        self.assertEqual(result, ["axa", "bxb"])

    def test_delete_only_remaining_line_content(self):
        # All lines present but content deleted
        cmds = self._check(["hello", "world"], ["", "world"], 0, 0, 0)
        self.assertIsNotNone(cmds)
        result = _apply(["hello", "world"], cmds, 0)
        self.assertEqual(result, ["", "world"])

    def test_join_lines(self):
        # J command: two lines joined into one
        cmds = self._check(["hello", "world"], ["helloworld"], 0, 0, 5)
        self.assertIsNotNone(cmds)
        result = _apply(["hello", "world"], cmds, 0)
        self.assertEqual(result, ["helloworld"])


class TestOnBytesToEdits(unittest.TestCase):
    """Test _on_bytes_to_edits for Neovim on_bytes event translation."""

    def test_single_char_insert(self):
        # Type "x" at (5,3)
        event = (5, 3, 0, 0, 0, 1)
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["helxlo"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [("I", 5, 3, "x")])

    def test_enter(self):
        # Enter at (5,3): splits line
        event = (5, 3, 0, 0, 1, 0)
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["hel", "lo"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [("I", 5, 3, "\n")])

    def test_backspace(self):
        # Backspace at (5,3): deletes char at (5,2)
        event = (5, 2, 0, 1, 0, 0)
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["helo"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [("D", 5, 2, "l")])

    def test_delete_line_dd(self):
        # dd on line "hello" at row 5
        event = (5, 0, 1, 0, 0, 0)
        old_lines = ["hello", "world"]
        new_buf = [""] * 5 + ["world"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [("D", 5, 0, "hello"), ("D", 5, 0, "\n")])

    def test_multi_line_paste(self):
        # Paste "abc\ndef" at (5,3)
        event = (5, 3, 0, 0, 1, 3)
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["helabc", "deflo"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(
            cmds,
            [
                ("I", 5, 3, "abc"),
                ("I", 5, 6, "\n"),
                ("I", 6, 0, "def"),
            ],
        )

    def test_visual_replace(self):
        # Visual replace "ello" with "i" at (5,1)
        event = (5, 1, 0, 4, 0, 1)
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["hio"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(
            cmds,
            [
                ("D", 5, 1, "ello"),
                ("I", 5, 1, "i"),
            ],
        )

    def test_multi_line_deletion(self):
        # Delete lines 5-6 ("hello\nworld" -> cursor at line 5, col 0, deletes 2 lines worth)
        event = (5, 0, 2, 0, 0, 0)
        old_lines = ["hello", "world", "end"]
        new_buf = [""] * 5 + ["end"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(
            cmds,
            [
                ("D", 5, 0, "hello"),
                ("D", 5, 0, "\n"),
                ("D", 5, 0, "world"),
                ("D", 5, 0, "\n"),
            ],
        )

    def test_no_change(self):
        event = (5, 0, 0, 0, 0, 0)
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["hello"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [])

    def test_multi_line_visual_replace(self):
        # Replace "llo\nwor" with "X" — (5,2) old=(1,3) new=(0,1)
        event = (5, 2, 1, 3, 0, 1)
        old_lines = ["hello", "world"]
        new_buf = [""] * 5 + ["heXld"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(
            cmds,
            [
                ("D", 5, 2, "llo"),
                ("D", 5, 2, "\n"),
                ("D", 5, 2, "wor"),
                ("I", 5, 2, "X"),
            ],
        )

    def test_utf8_insert_after_umlauts(self):
        # "te üü " is 8 bytes (t=1, e=1, space=1, ü=2, ü=2, space=1) and 6 chars.
        # Inserting "h" at byte position 8 = char position 6.
        event = (5, 8, 0, 0, 0, 1)
        old_lines = ["te üü world"]
        new_buf = [""] * 5 + ["te üü hworld"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [("I", 5, 6, "h")])

    def test_utf8_replace_in_umlaut_string(self):
        # Replace "world" with "h" at byte 8 = char 6
        # Old: "te üü world" (13 bytes, 11 chars)
        # New: "te üü h" (9 bytes, 7 chars)
        event = (5, 8, 0, 5, 0, 1)
        old_lines = ["te üü world"]
        new_buf = [""] * 5 + ["te üü h"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [("D", 5, 6, "world"), ("I", 5, 6, "h")])

    def test_utf8_delete_umlaut(self):
        # Delete one "ü" (2 bytes) at byte position 3 (char position 3)
        # Old: "te üü world", new: "te ü world"
        event = (5, 3, 0, 2, 0, 0)
        old_lines = ["te üü world"]
        new_buf = [""] * 5 + ["te ü world"]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertEqual(cmds, [("D", 5, 3, "ü")])

    def test_bounds_violation_returns_none(self):
        # Multi-line deletion extending past snippet boundary
        # Snippet has 3 lines, but old_end_row=2 + start_col=0 means we'd
        # need a 4th line for the trailing slice
        event = (1, 0, 2, 0, 0, 0)
        old_lines = ["hello", "nice", "world"]  # 3 lines
        new_buf = ["", ""]  # not relevant
        # rel_row=1, old_end_row=2, rel_row + old_end_row = 3 = len(old_lines)
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 0)
        self.assertIsNone(cmds)

    def test_bounds_change_above_snippet_returns_none(self):
        # Change at row 3, but snippet starts at row 5
        event = (3, 0, 0, 1, 0, 0)
        old_lines = ["hello"]
        new_buf = [""] * 3 + [""]
        cmds = _on_bytes_to_edits(event, old_lines, new_buf, 5)
        self.assertIsNone(cmds)


class TestListenerToEdits(unittest.TestCase):
    """Test _listener_to_edits for Vim listener_add event translation."""

    def _check(self, event, old_lines, new_buf, snippet_start, cursor_line, cursor_col):
        cmds = _listener_to_edits(
            event, old_lines, new_buf, snippet_start, cursor_line, cursor_col
        )
        self.assertIsNotNone(cmds, "_listener_to_edits returned None (gave up)")
        result = _apply(old_lines, cmds, snippet_start)
        # Build expected new_lines from the snippet region in new_buf
        added = int(event["added"])
        new_end = snippet_start + len(old_lines) + added
        expected = list(new_buf[snippet_start:new_end])
        self.assertEqual(
            result, expected, f"Commands {cmds} did not produce expected result"
        )
        return cmds

    def test_single_line_char_insert(self):
        # Type "x" on line 5 (1-indexed lnum=6, end=7, added=0)
        event = {"lnum": "6", "end": "7", "added": "0"}
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["helxlo"]
        cmds = self._check(event, old_lines, new_buf, 5, 5, 4)
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0][0], "I")

    def test_single_line_backspace(self):
        # Backspace on line 5 (lnum=6, end=7, added=0)
        event = {"lnum": "6", "end": "7", "added": "0"}
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["helo"]
        cmds = self._check(event, old_lines, new_buf, 5, 5, 3)
        self.assertEqual(cmds, [("D", 5, 3, "l")])

    def test_line_deletion_dd(self):
        # dd on "bbb" at buffer line 7 (1-indexed), snippet starts at line 5 (0-indexed)
        event = {"lnum": "7", "end": "8", "added": "-1"}
        old_lines = ["aaa", "bbb", "ccc"]
        new_buf = [""] * 5 + ["aaa", "ccc"]
        cmds = self._check(event, old_lines, new_buf, 5, 6, 0)
        result = _apply(["aaa", "bbb", "ccc"], cmds, 5)
        self.assertEqual(result, ["aaa", "ccc"])

    def test_enter_split(self):
        # Enter on line 6 (1-indexed): lnum=6, end=7, added=1
        event = {"lnum": "6", "end": "7", "added": "1"}
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["hel", "lo"]
        cmds = self._check(event, old_lines, new_buf, 5, 6, 0)
        result = _apply(["hello"], cmds, 5)
        self.assertEqual(result, ["hel", "lo"])

    def test_multi_line_snippet_scoped_to_changed_line(self):
        # Snippet has 3 lines, only middle line changed
        event = {"lnum": "7", "end": "8", "added": "0"}
        old_lines = ["aaa", "bbb", "ccc"]
        new_buf = [""] * 5 + ["aaa", "bxb", "ccc"]
        cmds = self._check(event, old_lines, new_buf, 5, 6, 2)
        # Should produce edit only for line 6 (0-indexed)
        self.assertEqual(len(cmds), 2)  # D + I for the replacement

    def test_disambiguates_identical_lines(self):
        # Snippet: ["aaa", "bbb", "aaa"], delete middle line
        # Without scoping, trimming might be confused by identical "aaa" lines
        event = {"lnum": "7", "end": "8", "added": "-1"}
        old_lines = ["aaa", "bbb", "aaa"]
        new_buf = [""] * 5 + ["aaa", "aaa"]
        cmds = self._check(event, old_lines, new_buf, 5, 6, 0)
        result = _apply(["aaa", "bbb", "aaa"], cmds, 5)
        self.assertEqual(result, ["aaa", "aaa"])

    def test_change_outside_snippet_returns_none(self):
        # Change on line 3 but snippet starts at line 5
        event = {"lnum": "4", "end": "5", "added": "0"}
        old_lines = ["hello"]
        new_buf = [""] * 5 + ["hello"]
        cmds = _listener_to_edits(event, old_lines, new_buf, 5, 3, 0)
        self.assertIsNone(cmds)

    def test_multi_line_deletion(self):
        # Delete "bbb" and "ccc": buffer lines 7-8 (1-indexed), snippet starts at 5 (0-indexed)
        event = {"lnum": "7", "end": "9", "added": "-2"}
        old_lines = ["aaa", "bbb", "ccc", "ddd"]
        new_buf = [""] * 5 + ["aaa", "ddd"]
        cmds = self._check(event, old_lines, new_buf, 5, 6, 0)
        result = _apply(["aaa", "bbb", "ccc", "ddd"], cmds, 5)
        self.assertEqual(result, ["aaa", "ddd"])


if __name__ == "__main__":
    unittest.main()
