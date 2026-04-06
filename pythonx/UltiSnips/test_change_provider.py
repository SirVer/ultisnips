#!/usr/bin/env python3

import unittest

from UltiSnips.change_provider import _edits_for_line_range, _line_diff


def transform(lines, cmds, start=0):
    """Apply edit commands to a list of lines and return the result.

    Edit commands use absolute line numbers; `start` is subtracted to get
    the index into the local buffer.
    """
    buf = list(lines)
    for cmd in cmds:
        ctype, line, col, char = cmd
        line -= start
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


class TestLineDiff(unittest.TestCase):
    def test_single_char_insert(self):
        cmds = _line_diff("hello", "helllo", 5)
        self.assertEqual(cmds, [("I", 5, 4, "l")])

    def test_single_char_delete(self):
        cmds = _line_diff("hello", "helo", 0)
        self.assertEqual(cmds, [("D", 0, 3, "l")])

    def test_replace(self):
        cmds = _line_diff("hello", "hallo", 0)
        self.assertEqual(cmds, [("D", 0, 1, "e"), ("I", 0, 1, "a")])

    def test_no_change(self):
        cmds = _line_diff("hello", "hello", 0)
        self.assertEqual(cmds, [])

    def test_complete_replacement(self):
        cmds = _line_diff("abc", "xyz", 0)
        self.assertEqual(cmds, [("D", 0, 0, "abc"), ("I", 0, 0, "xyz")])

    def test_insert_at_end(self):
        cmds = _line_diff("hi", "hi!", 0)
        self.assertEqual(cmds, [("I", 0, 2, "!")])

    def test_delete_from_end(self):
        cmds = _line_diff("hi!", "hi", 0)
        self.assertEqual(cmds, [("D", 0, 2, "!")])

    def test_empty_to_content(self):
        cmds = _line_diff("", "hello", 3)
        self.assertEqual(cmds, [("I", 3, 0, "hello")])

    def test_content_to_empty(self):
        cmds = _line_diff("hello", "", 3)
        self.assertEqual(cmds, [("D", 3, 0, "hello")])


class TestEditsForLineRange(unittest.TestCase):
    """Test _edits_for_line_range produces correct edit sequences."""

    def _check(self, old, new, start=0):
        """Verify that the produced edits transform old into new."""
        cmds = _edits_for_line_range(old, new, start)
        result = transform(old, cmds, start)
        self.assertEqual(result, new, f"cmds={cmds}")

    def test_no_change(self):
        cmds = _edits_for_line_range(["a", "b"], ["a", "b"], 0)
        self.assertEqual(cmds, [])

    def test_single_line_edit(self):
        self._check(["hello world"], ["hello there"])

    def test_single_char_insert(self):
        self._check(["hi"], ["hix"])

    def test_delete_one_line(self):
        self._check(["a", "b", "c"], ["a", "c"])

    def test_delete_first_line(self):
        self._check(["a", "b", "c"], ["b", "c"])

    def test_delete_last_line(self):
        self._check(["a", "b", "c"], ["a", "b"])

    def test_delete_all_lines_but_one(self):
        self._check(["a", "b", "c"], ["a"])

    def test_insert_one_line_returns_none(self):
        """Line insertion returns None to signal fallback to guess_edit."""
        cmds = _edits_for_line_range(["a", "c"], ["a", "b", "c"], 0)
        self.assertIsNone(cmds)

    def test_insert_at_end_returns_none(self):
        cmds = _edits_for_line_range(["a", "b"], ["a", "b", "c"], 0)
        self.assertIsNone(cmds)

    def test_insert_multiple_lines_returns_none(self):
        cmds = _edits_for_line_range(["a"], ["a", "b", "c", "d"], 0)
        self.assertIsNone(cmds)

    def test_replace_line(self):
        self._check(["a", "old", "c"], ["a", "new", "c"])

    def test_with_start_offset(self):
        self._check(["hi", "world", "end"], ["hi", "end"], start=2)

    def test_delete_middle_line_with_offset(self):
        """The specific case from the dd test."""
        old = ["hi", "world", "end"]
        new = ["hi", "end"]
        cmds = _edits_for_line_range(old, new, 2)
        result = transform(old, cmds, 2)
        self.assertEqual(result, new)
        # Content should be deleted before newline (critical for _do_edit).
        content_dels = [c for c in cmds if c[0] == "D" and c[3] != "\n"]
        newline_dels = [c for c in cmds if c[0] == "D" and c[3] == "\n"]
        if content_dels and newline_dels:
            # First content delete should come before first newline delete.
            first_content_idx = cmds.index(content_dels[0])
            first_newline_idx = cmds.index(newline_dels[0])
            self.assertLess(first_content_idx, first_newline_idx)

    def test_complex_mixed_change(self):
        self._check(["a", "b", "c", "d"], ["a", "X", "Y", "d"])

    def test_empty_old_line(self):
        self._check(["", "b"], ["a", "b"])

    def test_empty_new_line(self):
        self._check(["a", "b"], ["", "b"])


if __name__ == "__main__":
    unittest.main()
