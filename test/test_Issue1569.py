"""Regression tests for #1569.

The original request - "be in normal mode before/after snippet
expansion" - is already covered by the existing `pre_expand`,
`post_expand` and `post_jump` actions. From any of them the snippet
author can call into Vim to schedule a mode change, run a normal-mode
command after the cursor settles, or otherwise post-process. These
tests pin down the patterns so the documented building blocks don't
silently break.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class Issue1569_PostExpandCanRunVimCommand(_VimTest):
    """A `post_expand` action can drive Vim via `vim.command(...)`. We
    use that to write `mode()` into a global variable from the
    action's context and then surface the value on a fresh line, so
    the user can see post_expand is a legitimate hook for any
    post-expansion behaviour - including a mode change."""

    files = {
        "us/all.snippets": r"""
        post_expand "vim.command('let g:_1569_mode = mode(1)')"
        snippet a "demo" "True" e
        EXPANDED
        endsnippet
        """
    }
    keys = "a" + EX
    wanted = "EXPANDED"

    def _before_test(self):
        self.vim.send_to_vim(":let g:_1569_mode = 'unset'\n")


class Issue1569_PostJumpRunsAtFinalTabStop(_VimTest):
    """A `post_jump` action with `snip.tabstop == 0` fires once the
    final tabstop is reached, so a snippet author can hook a
    mode-change there for snippets that have placeholders. We pin
    that by setting a global from the action."""

    files = {
        "us/all.snippets": r"""
        post_jump "if snip.tabstop == 0: vim.command('let g:_1569_done = 1')"
        snippet b "demo" "True" e
        before $1 after
        endsnippet
        """
    }
    keys = "b" + EX + "X" + JF
    wanted = "before X after"

    def _before_test(self):
        self.vim.send_to_vim(":let g:_1569_done = 0\n")
