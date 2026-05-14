"""Regression test for `:UltiSnipsEdit` when the snippets directory is
reached through a symlink (GH #1543).

The non-bang `:UltiSnipsEdit` path checks that each candidate snippet
directory sits inside one of the user's vim config directories. When
either leg of that comparison goes through a symlink (a symlinked
`UltiSnips/` dir, or a `$HOME` that the OS resolves to a different
mountpoint), the unresolved string compare missed the match and
`:UltiSnipsEdit` reported "UltiSnips was not able to find a default
directory for snippets". The test routes the dot-vim discovery through
a symlinked `$HOME`/`$XDG_CONFIG_HOME` so the regression path is forced.
"""

import contextlib

from test.vim_test_case import VimTestCase as _VimTest


class UltiSnipsEdit_SymlinkedConfigHome_FindsSnippet(_VimTest):
    keys = ""
    text_before = ""
    text_after = ""

    @property
    def wanted(self):
        return self._expected_file

    def _extra_vim_config(self, vim_config):
        # Lay out a real snippets directory, a dot-vim home, and a symlink
        # from the dot-vim home into the snippets directory. Then route
        # $HOME through a symlinked alias of `self._temp_dir` so
        # `get_dot_vim()` (which resolves) and `find_all_snippet_directories()`
        # (which doesn't) disagree on the path layout (#1543).
        snippets_target = self._temp_dir / "real_snippets"
        snippets_target.mkdir(parents=True, exist_ok=True)
        (snippets_target / "python.snippets").write_text(
            'snippet hi "" b\nhello\nendsnippet\n'
        )

        dot_vim = self._temp_dir / ".vim"
        dot_vim.mkdir(parents=True, exist_ok=True)
        link = dot_vim / "UltiSnips"
        with contextlib.suppress(FileExistsError):
            link.symlink_to(snippets_target, target_is_directory=True)

        sym_home = self._temp_dir.parent / (self._temp_dir.name + "_home_sym")
        with contextlib.suppress(FileExistsError):
            sym_home.symlink_to(self._temp_dir, target_is_directory=True)

        vim_config.append(f"let $HOME = '{sym_home}'")
        vim_config.append(f"set runtimepath+={sym_home}/.vim")
        # Two-entry list forces the multi-dir branch in `_file_to_edit`,
        # which is the one that does the parent vs. dot-vim comparison.
        vim_config.append(
            f"let g:UltiSnipsSnippetDirectories=['{sym_home}/.vim/UltiSnips', 'UltiSnips']"
        )

        self._expected_file = str((snippets_target / "python.snippets").resolve())

    def _before_test(self):
        helper = self._temp_dir / "_run_edit.py"
        helper.write_text(
            "import traceback, vim\n"
            "from UltiSnips.snippet_manager import UltiSnips_Manager\n"
            "try:\n"
            "    out = UltiSnips_Manager._file_to_edit('python', '')\n"
            "except Exception:\n"
            "    out = traceback.format_exc()\n"
            "vim.current.buffer[:] = (str(out) or '<empty>').splitlines()\n"
        )
        self.vim.send_to_vim(f":py3file {helper}\n")
