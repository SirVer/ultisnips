"""Unit tests for ulti_snips snippet source helpers.

Regression coverage for https://github.com/SirVer/ultisnips/issues/1483:
``find_all_snippet_directories()`` must not resolve symlinks when walking
'runtimepath', otherwise a symlinked ``~/.vim/UltiSnips`` directory breaks
``:UltiSnipsEdit`` (its ``.parent`` no longer equals ``~/.vim``).
"""

from pathlib import Path
from unittest.mock import patch

from UltiSnips.snippet.source.file.ulti_snips import find_all_snippet_directories


def _make_vim_eval(runtimepath, snippet_dirs):
    """Returns a ``vim.eval`` replacement that answers just the calls
    ``find_all_snippet_directories`` makes."""

    def _eval(expr):
        if expr == "exists('b:UltiSnipsSnippetDirectories')":
            return "0"
        if expr == "g:UltiSnipsSnippetDirectories":
            return list(snippet_dirs)
        if expr == "&runtimepath":
            return ",".join(runtimepath)
        raise AssertionError(f"unexpected vim.eval({expr!r})")

    return _eval


def test_symlinked_snippet_dir_is_not_resolved(tmp_path):
    """A symlinked ``UltiSnips`` directory under an rtp entry should be
    returned as-is, with its parent still equal to the rtp entry. Regression
    for issue #1483 — earlier code called ``normalize_file_path`` on the
    joined path, which resolved the symlink and made the subsequent
    ``Path(snippet_dir).parent == dot_vim_dir`` check in ``_snippets_for_edit``
    always fail.
    """
    dot_vim = tmp_path / "home" / ".vim"
    dot_vim.mkdir(parents=True)
    real_snippets = tmp_path / "dot-files" / "UltiSnips"
    real_snippets.mkdir(parents=True)
    link = dot_vim / "UltiSnips"
    link.symlink_to(real_snippets)

    with patch(
        "UltiSnips.vim_helper.eval",
        side_effect=_make_vim_eval([str(dot_vim)], ["UltiSnips"]),
    ):
        found = find_all_snippet_directories()

    assert found == [str(link)], (
        f"expected the rtp-relative (unresolved) path to be returned, got {found!r}"
    )
    assert Path(found[0]).parent == dot_vim, (
        "parent of the returned path must still equal the rtp entry; "
        "if this fails, :UltiSnipsEdit will reject the dir in _snippets_for_edit"
    )
