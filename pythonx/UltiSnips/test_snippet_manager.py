#!/usr/bin/env python3

"""Unit tests for pure-Python helpers in snippet_manager.

The `vim` module is mocked by pythonx/conftest.py so these run without Vim.
"""

import unittest

from UltiSnips.snippet_manager import _trigger_roundtrips_as_text


class TriggerRoundtripsAsText(unittest.TestCase):
    """Regression tests for the trigger-key fallthrough cluster:
    #1523 (<a-;>), #1482 (<c-space>), #1460 (<c-j>), #1232 (<space>).

    `_handle_failure` re-emits the trigger as buffer text via :return through
    the <C-R>=…<cr> mapping. For special <…> keys, that text is either a
    vim-internal multi-byte key code (shows as garbage like <t_ü>) or a
    control character (LF for <c-j>) that overrides user intent. The helper
    decides which triggers are safe to re-emit; <tab>/<s-tab> are handled
    separately in _handle_failure and never reach this helper.
    """

    def test_space_is_safe(self):
        # <space> is the lone <…>-form trigger that roundtrips cleanly.
        self.assertTrue(_trigger_roundtrips_as_text("<space>"))
        self.assertTrue(_trigger_roundtrips_as_text("<SPACE>"))

    def test_ctrl_j_is_unsafe(self):
        # #1460: \<c-j> = LF would split the line and bypass `imap <c-j> <nop>`.
        self.assertFalse(_trigger_roundtrips_as_text("<c-j>"))
        self.assertFalse(_trigger_roundtrips_as_text("<C-J>"))

    def test_ctrl_space_is_unsafe(self):
        # #1482: \<c-space> evaluates to vim-internal bytes shown as <t_ü>.
        self.assertFalse(_trigger_roundtrips_as_text("<c-space>"))

    def test_alt_semicolon_is_unsafe(self):
        # #1523: \<a-;> evaluates to vim-internal bytes shown as <t_u;>.
        self.assertFalse(_trigger_roundtrips_as_text("<a-;>"))

    def test_function_keys_are_unsafe(self):
        self.assertFalse(_trigger_roundtrips_as_text("<F2>"))
        self.assertFalse(_trigger_roundtrips_as_text("<f12>"))

    def test_literal_chars_are_safe(self):
        # Literal-character triggers continue to roundtrip cleanly.
        self.assertTrue(_trigger_roundtrips_as_text(";"))
        self.assertTrue(_trigger_roundtrips_as_text("*"))


if __name__ == "__main__":
    unittest.main()
