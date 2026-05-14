"""Tests for `:UltiSnipsRemoveFiletypes` (GH #792).

Removes the snippets that come from a filetype the buffer would otherwise
inherit (via `&filetype`, via a previous `:UltiSnipsAddFiletypes`, or the
implicit `all`).
"""

from test.constant import EX
from test.vim_test_case import VimTestCase as _VimTest


class RemoveFiletypes_DisablesInheritedFiletype(_VimTest):
    """`set filetype=html.css` brings in both html and css snippets;
    `:UltiSnipsRemoveFiletypes html` should suppress the html one."""

    files = {
        "us/html.snippets": r"""
        snippet ftrm "html"
        FROM_HTML
        endsnippet
        """,
        "us/css.snippets": r"""
        snippet ftrm "css"
        FROM_CSS
        endsnippet
        """,
    }

    def _before_test(self):
        self.vim.send_to_vim(":set filetype=html.css\n")
        self.vim.send_to_vim(":UltiSnipsRemoveFiletypes html\n")

    keys = "ftrm" + EX
    wanted = "FROM_CSS"


class RemoveFiletypes_RestoredByAdd(_VimTest):
    """A subsequent `:UltiSnipsAddFiletypes` re-enables a previously removed
    filetype."""

    files = {
        "us/html.snippets": r"""
        snippet ftrm "html"
        FROM_HTML
        endsnippet
        """,
    }

    def _before_test(self):
        self.vim.send_to_vim(":set filetype=html\n")
        self.vim.send_to_vim(":UltiSnipsRemoveFiletypes html\n")
        self.vim.send_to_vim(":UltiSnipsAddFiletypes html\n")

    keys = "ftrm" + EX
    wanted = "FROM_HTML"


class RemoveFiletypes_DisablesAddedFiletype(_VimTest):
    """A filetype injected through `:UltiSnipsAddFiletypes` can also be
    removed."""

    files = {
        "us/extra.snippets": r"""
        snippet ftrm "extra"
        FROM_EXTRA
        endsnippet
        """,
    }

    def _before_test(self):
        self.vim.send_to_vim(":UltiSnipsAddFiletypes extra\n")
        self.vim.send_to_vim(":UltiSnipsRemoveFiletypes extra\n")

    keys = "ftrm" + EX
    wanted = "ftrm" + EX
