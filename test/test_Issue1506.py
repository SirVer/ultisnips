"""Tests for #1506.

`UltiSnips#FindAutoTriggerConflicts()` walks the snippets visible in
the current scope and returns the pairs ``(short, long)`` where the
short trigger fires automatically (``A`` option) and is a literal
prefix of the long trigger - so the long one can never fire because
the autotrigger ``short`` snaps first.
"""

from test.vim_test_case import VimTestCase as _VimTest


class Issue1506_NoConflictsWhenTriggersAreDisjoint(_VimTest):
    """Two autotrigger snippets with unrelated trigger words: no
    conflicts."""

    files = {
        "us/all.snippets": r"""
        snippet alpha "" "True" Ae
        ALPHA
        endsnippet
        snippet beta "" "True" Ae
        BETA
        endsnippet
        """
    }
    keys = ""
    text_before = ""
    text_after = ""
    wanted = "[]"

    def _before_test(self):
        self.vim.send_to_vim(
            ":call setline('.', string(UltiSnips#FindAutoTriggerConflicts()))\n"
        )


class Issue1506_DetectsAutoShadowingNonAuto(_VimTest):
    """`bs` is autotriggered; `bst` is a plain (TAB-triggered) snippet.
    The user can never reach `bst` because typing 'bs' fires `bs`
    first - this is the original bug-report scenario."""

    files = {
        "us/all.snippets": r"""
        snippet bs "" "True" Ae
        BS
        endsnippet
        snippet bst "" "True" e
        BST
        endsnippet
        """
    }
    keys = ""
    text_before = ""
    text_after = ""
    wanted = "[['bs', 'bst']]"

    def _before_test(self):
        self.vim.send_to_vim(
            ":call setline('.', string(UltiSnips#FindAutoTriggerConflicts()))\n"
        )


class Issue1506_DetectsAutoShadowingAuto(_VimTest):
    """Both `bs` and `bst` are autotriggered. `bs` fires first, so
    `bst` is shadowed. Conflict reported."""

    files = {
        "us/all.snippets": r"""
        snippet bs "" "True" Ae
        BS
        endsnippet
        snippet bst "" "True" Ae
        BST
        endsnippet
        """
    }
    keys = ""
    text_before = ""
    text_after = ""
    wanted = "[['bs', 'bst']]"

    def _before_test(self):
        self.vim.send_to_vim(
            ":call setline('.', string(UltiSnips#FindAutoTriggerConflicts()))\n"
        )


class Issue1506_NonAutoPrefixIsNotAConflict(_VimTest):
    """If the short trigger is *not* an autotrigger, there is no
    conflict: the user has to press TAB explicitly, so they can type
    past `bs` to reach `bst`."""

    files = {
        "us/all.snippets": r"""
        snippet bs "" "True" e
        BS
        endsnippet
        snippet bst "" "True" Ae
        BST
        endsnippet
        """
    }
    keys = ""
    text_before = ""
    text_after = ""
    wanted = "[]"

    def _before_test(self):
        self.vim.send_to_vim(
            ":call setline('.', string(UltiSnips#FindAutoTriggerConflicts()))\n"
        )


class Issue1506_IgnoresRegexTriggers(_VimTest):
    """Regex triggers are skipped: prefix containment isn't a
    well-defined relationship for them."""

    files = {
        "us/all.snippets": r"""
        snippet xy "" "True" Ae
        XY
        endsnippet
        snippet "xy.*" "" "True" rAe
        XY_REGEX
        endsnippet
        """
    }
    keys = ""
    text_before = ""
    text_after = ""
    wanted = "[]"

    def _before_test(self):
        self.vim.send_to_vim(
            ":call setline('.', string(UltiSnips#FindAutoTriggerConflicts()))\n"
        )
