"""Verify the scratch-buffer error display stays focused on what the user
needs to fix, not on UltiSnips internals.

Before: a raise inside a user's `!p` block dumped the full UltiSnips
internal stack trace from `expand` -> `_try_expand` -> ... into the
scratch buffer, drowning the actual exception message and the offending
snippet line.

Now: only the exception type/message and the offending snippet code are
shown. The full traceback path remains for genuinely-unattributed
exceptions (real UltiSnips bugs).
"""

from test.constant import EX
from test.vim_test_case import VimTestCase as _VimTest


class ErrorReporting_SnippetCodeIsConcise(_VimTest):
    files = {
        "us/all.snippets": """
snippet bad "Bad snippet"
`!p snip.rv = 1 / 0`
endsnippet
"""
    }
    keys = "bad" + EX
    expected_error = (
        r"(?s)UltiSnips Error:\s+ZeroDivisionError: division by zero.*"
        r"Executed snippet code:"
    )
    forbidden_in_error = r"Following is the full stack trace"
