"""Regression tests for #1305.

`UltiSnips#CanExpandSnippet()`, `UltiSnips#CanJumpForwards()` and
`UltiSnips#CanJumpBackwards()` are the documented entry points for
callers that want to know whether an expand/jump would do anything
before they commit to the `<C-R>=...<CR>` round-trip that actually
performs it. The bug report tripped over calling the action-taking
entry point inside a Lua `:expr` context where the buffer cannot be
modified; the predicate trio is what the caller actually needed. These
tests pin the predicates' return values so they don't silently
regress.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest

_SNIPPETS = ("abc", "expanded $1 then $2")

# <C-R>=<expr><CR>: evaluate <expr> in normal expression context and
# insert the result at the cursor. The result must be a string so the
# value is preserved verbatim.
CR = "\x12"  # ^R
NL = "\r"


def _probe(label, expr):
    """Insert `<label>=<result>` at the cursor without leaving insert mode."""
    return f'{CR}=printf("{label}=%d", {expr}){NL}'


class Issue1305_Smoke_SnippetExpands(_VimTest):
    """Sanity check: the fixture snippet expands via TAB the normal way."""

    snippets = _SNIPPETS
    keys = "abc" + EX + "X" + JF + "Y"
    wanted = "expanded X then Y"


class Issue1305_CanExpand_NoTrigger(_VimTest):
    """At a clean position with no trigger before the cursor,
    `UltiSnips#CanExpandSnippet()` is 0."""

    snippets = _SNIPPETS
    keys = _probe("ce", "UltiSnips#CanExpandSnippet()")
    wanted = "ce=0"


class Issue1305_CanExpand_AfterTrigger(_VimTest):
    """With the trigger typed and the cursor right after it,
    `UltiSnips#CanExpandSnippet()` is 1 and the predicate does NOT
    consume the trigger -- the trigger text "abc" is still present so
    a subsequent `<C-R>=UltiSnips#ExpandSnippet()<CR>` will pick it up
    and expand the snippet."""

    snippets = _SNIPPETS
    keys = "abc" + _probe("ce", "UltiSnips#CanExpandSnippet()")
    wanted = "abcce=1"


class Issue1305_CanJump_BeforeAnyExpansion(_VimTest):
    """With no active snippet, the jump predicates are both 0."""

    snippets = _SNIPPETS
    keys = _probe("cf", "UltiSnips#CanJumpForwards()") + _probe(
        "cb", "UltiSnips#CanJumpBackwards()"
    )
    wanted = "cf=0cb=0"


class Issue1305_CanJumpForwards_AfterFillingFirstTabStop(_VimTest):
    """After expanding and typing into $1, the cursor sits inside an
    active snippet with another tabstop ahead. Forward jump is
    available; backward jump is not because $1 is already the first
    tabstop in the snippet."""

    snippets = _SNIPPETS
    keys = (
        "abc"
        + EX
        + "first"
        + _probe("cf", "UltiSnips#CanJumpForwards()")
        + _probe("cb", "UltiSnips#CanJumpBackwards()")
    )
    wanted = "expanded firstcf=1cb=0 then "


class Issue1305_CanJump_AfterSnippetCompletes(_VimTest):
    """Once the user has jumped past the last tabstop, the snippet is
    torn down and both jump predicates are 0 -- the user knows it is
    safe to fall through to whatever the trigger key would otherwise
    do (e.g. insert a tab)."""

    snippets = _SNIPPETS
    keys = (
        "abc"
        + EX
        + "first"
        + JF
        + "second"
        + JF
        + _probe("cf", "UltiSnips#CanJumpForwards()")
        + _probe("cb", "UltiSnips#CanJumpBackwards()")
    )
    wanted = "expanded first then secondcf=0cb=0"
