"""Regression tests for the "Multiple matches" dialog appearing on a single
snippet (issues #1341, #1519, #1559).

The same snippet file can end up being parsed twice — either because the
runtimepath contains a symlinked copy of the same directory, or because the
file is picked up via the `<ft>_*.snippets` glob for one filetype and again as
the canonical file for another filetype that is referenced from `extends`.
Both cases used to surface as the inputlist() prompt showing the same snippet
twice, even when the choices were indistinguishable.
"""

import contextlib

from test.constant import ESC, EX
from test.vim_test_case import VimTestCase as _VimTest


class DuplicateSnippets_ExtendsSubFile(_VimTest):
    # `foo.snippets` extends a filetype whose name (`foo_bar`) collides with
    # the `foo_*.snippets` sub-file convention. The same file used to be
    # parsed under both filetypes and `foo_bar` showed up twice.
    files = {
        "us/foo.snippets": r"""
        extends foo_bar
        """,
        "us/foo_bar.snippets": r"""
        snippet hi "Greeting"
        hello
        endsnippet
        """,
    }
    keys = ESC + ":set ft=foo\n" + "ihi" + EX
    wanted = "hello"


class DuplicateSnippets_ExtendsWithSnippetsSuffix(_VimTest):
    # `extends` takes a filetype name; including the `.snippets` extension is
    # a common user mistake. Be lenient and strip it.
    files = {
        "us/foo.snippets": r"""
        extends foo_bar.snippets
        """,
        "us/foo_bar.snippets": r"""
        snippet hi "Greeting"
        hello
        endsnippet
        """,
    }
    keys = ESC + ":set ft=foo\n" + "ihi" + EX
    wanted = "hello"


class DuplicateSnippets_SymlinkedRuntimepath(_VimTest):
    # A symlink that exposes the temp dir under a second path means the same
    # snippet file is reached via two distinct string paths. Path
    # canonicalization in `find_all_snippet_files` collapses them.
    files = {
        "us/foo.snippets": r"""
        snippet hi "Greeting"
        hello
        endsnippet
        """,
    }
    keys = ESC + ":set ft=foo\n" + "ihi" + EX
    wanted = "hello"

    def _extra_vim_config(self, vim_config):
        sym = self._temp_dir.parent / (self._temp_dir.name + "_sym")
        with contextlib.suppress(FileExistsError):
            sym.symlink_to(self._temp_dir, target_is_directory=True)
        vim_config.append(f"set runtimepath+={sym}")


class DuplicateSnippets_DoesNotMergeDistinctTriggers(_VimTest):
    # Two genuinely different snippets sharing a trigger from different
    # filetypes must still produce the inputlist() prompt — the dedupe must
    # only suppress copies of the *same* snippet definition.
    files = {
        "us/a.snippets": r"""
        snippet hi "Greeting from a"
        from_a
        endsnippet
        """,
        "us/b.snippets": r"""
        extends a
        snippet hi "Greeting from b"
        from_b
        endsnippet
        """,
    }
    # Buffer filetype `b` is listed first by `get_deep_extends`, so b's
    # snippet appears as option 1 in the prompt and a's as option 2.
    keys = ESC + ":set ft=b\n" + "ihi" + EX + "2\n"
    wanted = "from_a"
