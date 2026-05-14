"""Regression test for #1572.

The dot operator (`.`) repeats the *last text-changing normal-mode
command*. UltiSnips applies a snippet expansion through Vim's Python
API, which writes into the buffer outside Vim's keystroke-recording
machinery; only the text the user types *after* the expansion is part
of the last change as far as Vim is concerned. As a consequence, `.`
re-types whatever the user inserted into placeholders, but does not
re-fire the snippet itself.

This is a fundamental limitation of how UltiSnips integrates with Vim's
change tracking. The test pins the current behaviour so any future
attempt to "support `.`" has to acknowledge the existing semantics it is
changing.
"""

from test.constant import ESC, EX
from test.vim_test_case import VimTestCase as _VimTest


class Issue1572_DotDoesNotReExpandSnippet(_VimTest):
    """Pressing `.` after a snippet expansion does NOT re-expand the
    trigger. The dot operator only repeats the visible last change,
    which is whatever the user typed after UltiSnips wrote the snippet
    body into the buffer."""

    snippets = ("abc", "EXPANDED")
    # Expand once via TAB, then move to a fresh line and hit `.`.
    keys = "abc" + EX + ESC + "o" + ESC + "."
    # The first line contains the actual expansion. The second line is
    # the result of pressing `.`, which repeats the *last change* --
    # here that's the empty insert produced by `o<Esc>`. If `.` had
    # somehow re-expanded the snippet, the line would say `EXPANDED`.
    wanted = "EXPANDED\n\n"
