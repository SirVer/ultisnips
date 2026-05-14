"""Regression test for the `ExpandPossibleShorterSnippet` example in
`:help UltiSnips#SnippetsInCurrentScope` (GH #951).

If a user copies the example verbatim, typing the shortened prefix should
expand the matching snippet with no extra characters appended.
"""

from test.vim_test_case import VimTestCase as _VimTest

EXPAND_SHORTER = chr(12)  # C-L, the keybinding the docs use.


class _ShorterSnippetBase(_VimTest):
    snippets = (("lorem", "Lorem ipsum dolor", "lorem ipsum"),)

    def _extra_vim_config(self, vim_config):
        vim_config.extend(
            [
                "function! ExpandPossibleShorterSnippet()",
                "  let snippets = UltiSnips#SnippetsInCurrentScope()",
                "  if len(snippets) != 1",
                "    return 0",
                "  endif",
                "  let trigger = keys(snippets)[0]",
                "  let [lnum, col] = [line('.'), col('.') - 1]",
                "  let line = getline(lnum)",
                "  let prefix_len = strlen(matchstr(strpart(line, 0, col), '\\k*$'))",
                "  let head = strpart(line, 0, col - prefix_len)",
                "  let tail = strpart(line, col)",
                "  call setline(lnum, head . trigger . tail)",
                "  call cursor(lnum, strlen(head . trigger) + 1)",
                "  return 1",
                "endfunction",
                "inoremap <silent> <C-L> <C-R>=(ExpandPossibleShorterSnippet() == 0? '': UltiSnips#ExpandSnippet())<CR>",
            ]
        )


class ShorterSnippet_Expands_NoTrailingSpace(_ShorterSnippetBase):
    keys = "lor" + EXPAND_SHORTER
    wanted = "Lorem ipsum dolor"


class ShorterSnippet_ExpandsAfterText(_ShorterSnippetBase):
    keys = "hello lo" + EXPAND_SHORTER
    wanted = "hello Lorem ipsum dolor"


class ShorterSnippet_NoExpand_WhenMultipleMatches(_VimTest):
    snippets = (
        ("lorem", "Lorem ipsum dolor", "lorem"),
        ("login", "user.login()", "login"),
    )
    keys = "lo" + EXPAND_SHORTER
    wanted = "lo"

    _extra_vim_config = _ShorterSnippetBase._extra_vim_config
