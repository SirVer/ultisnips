"""Tests for `UltiSnips#SnippetLocations` and `:UltiSnipsListLocations`
(GH #1198).
"""

from test.vim_test_case import VimTestCase as _VimTest

C_L = chr(12)  # <C-L>, used to dump the result into the buffer.


class SnippetLocations_ReturnsFileBackedSnippets(_VimTest):
    """`UltiSnips#SnippetLocations()` returns one quickfix-shaped entry per
    snippet defined in a file, with the trigger and description in `text`."""

    files = {
        "us/all.snippets": r"""
        snippet alpha "first one"
        AAA
        endsnippet

        snippet beta "second one"
        BBB
        endsnippet
        """
    }

    def _extra_vim_config(self, vim_config):
        vim_config.extend(
            [
                "function! S_DumpLocations()",
                "  let entries = UltiSnips#SnippetLocations()",
                "  return join(map(copy(entries),"
                ' \'v:val.text . "@" . fnamemodify(v:val.filename, ":t")'
                " . \":\" . v:val.lnum'), ',')",
                "endfunction",
                "inoremap <silent> <C-L> <C-R>=S_DumpLocations()<CR>",
            ]
        )

    keys = C_L
    wanted = "alpha - first one@all.snippets:2,beta - second one@all.snippets:6"


class SnippetLocations_OmitsProgrammaticSnippets(_VimTest):
    """Snippets added through `UltiSnips#AddSnippetWithPriority` carry the
    placeholder location 'added' (no `:line`) and should be skipped."""

    snippets = (("addedone", "AAA"),)
    files = {
        "us/all.snippets": r"""
        snippet onlyfile "from file"
        FFF
        endsnippet
        """
    }

    def _extra_vim_config(self, vim_config):
        vim_config.extend(
            [
                "function! S_DumpTriggers()",
                "  let entries = UltiSnips#SnippetLocations()",
                "  return join(map(copy(entries), 'v:val.text'), ',')",
                "endfunction",
                "inoremap <silent> <C-L> <C-R>=S_DumpTriggers()<CR>",
            ]
        )

    keys = C_L
    wanted = "onlyfile - from file"
