"""Regression tests for issue #751: junk characters appearing in snippet
expansions because the move command queued by `vim_helper.select()` ended up
typed as literal buffer text instead of executed.

The issue has two confirmed mechanisms, both reproducible on master before
this fix:

1. A `post_jump` action calls a typeahead-consuming Vim function (e.g.
   `vim.command('call input("pause")')`). `input()` swallows the leading
   `<Esc>` of the queued move command and the rest is then processed in the
   original insert mode, leaving e.g. `a` or `v3G10|o3G4|o` as literal text.
   This is Maelan's minimal repro (2018):
   https://github.com/SirVer/ultisnips/issues/751#issuecomment-421159566

2. A `post_jump` action calls `snip.expand_anon(...)` whose first tabstop is
   defaulted. The outer jump's mode-entry (`:startinsert`, scheduled) flips
   the mode to insert before the inner jump's queued visual-mode keys are
   processed, so the visual commands land in insert mode as text. This is
   the shape of nihlaeth's 2017 report:
   https://github.com/SirVer/ultisnips/issues/751#issuecomment-271122304

bpj's original 2016 repro (regex-trigger snippet with vim.bindeval) was not
reproducible on master even before this fix.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest

# Mechanism 1: post_jump action calls input()/getchar(), which swallows the
# queued <Esc> of the move command.


class PostJumpJunk_InputEmptyTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def test_snippet():
            vim.command('call input("pause")')
        endglobal

        post_jump "if snip.tabstop == 0: test_snippet()"
        snippet post
        [${1}][${0}]
        endsnippet
        """
    }
    # Append "\n" so the input("pause") call inside the post_jump action
    # gets its ENTER and returns; otherwise vim hangs at the prompt.
    keys = "post" + EX + JF + "\n"
    wanted = "[][]"


class PostJumpJunk_InputDefaultedTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def test_snippet():
            vim.command('call input("pause")')
        endglobal

        post_jump "if snip.tabstop == 0: test_snippet()"
        snippet postdef
        [${1}][${0:default}]
        endsnippet
        """
    }
    keys = "postdef" + EX + JF + "\n"
    wanted = "[][default]"


# Mechanism 2: post_jump action expands an anonymous snippet whose first
# tabstop has a default. The outer jump's deferred :startinsert flips the
# mode before the inner jump's visual-mode keys process, leaking them as
# buffer text.


class PostJumpJunk_ExpandAnonDefaultedFirstTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def insert_anon(snip):
            snip.expand_anon('${1:first} ${2:second}')
        endglobal

        post_jump "if snip.tabstop == 0: insert_anon(snip)"
        snippet def "function" bm
        def ${1:name}(): $0
        endsnippet
        """
    }
    # Expand `def`, accept the default name, jump to $0 (firing post_jump
    # which expands the anon). Then fill in the anon's two tabstops.
    keys = "def" + EX + JF + "a" + JF + "b"
    wanted = "def name(): a b"
