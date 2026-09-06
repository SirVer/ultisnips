#!/usr/bin/env python3

"""Tests for snippet directory discovery along 'runtimepath':
`find_all_snippet_directories` in snippet/source/file/ulti_snips.py and
`_snipmate_files_for` in snippet/source/file/snipmate.py.

Both read their configuration through `vim_helper.eval`, which is patched
here so they run without Vim. The `vim` module itself is mocked by
pythonx/conftest.py.
"""

import contextlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from UltiSnips.error import PebkacError
from UltiSnips.snippet.source.file import snipmate, ulti_snips


@contextlib.contextmanager
def _vim_config(runtimepath, snippet_dirs):
    """Answers the `vim_helper.eval` queries `find_all_snippet_directories`
    makes as if Vim had the given 'runtimepath' and
    g:UltiSnipsSnippetDirectories."""
    answers = {
        "exists('b:UltiSnipsSnippetDirectories')": "0",
        "g:UltiSnipsSnippetDirectories": list(snippet_dirs),
        "&runtimepath": ",".join(str(entry) for entry in runtimepath),
    }
    with mock.patch.object(
        ulti_snips.vim_helper, "eval", side_effect=answers.__getitem__
    ):
        yield


@contextlib.contextmanager
def _recording_scandir():
    """Records every directory that gets listed through `os.scandir`."""
    listed = []
    real_scandir = os.scandir

    def recording(path=".", *args, **kwargs):
        listed.append(str(path))
        return real_scandir(path, *args, **kwargs)

    with mock.patch.object(os, "scandir", recording):
        yield listed


class TestFindAllSnippetDirectories(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="UltiSnipsTest_dirs")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.bundle = self.root / "bundle"
        self.plugins = [self.bundle / f"plugin{i}" for i in range(5)]
        for plugin in self.plugins:
            plugin.mkdir(parents=True)
        # Only every other plugin ships snippets.
        self.with_snippets = [plugin / "UltiSnips" for plugin in self.plugins[::2]]
        for directory in self.with_snippets:
            directory.mkdir()

    def test_literal_entries_return_existing_directories_in_order(self):
        with _vim_config(self.plugins, ["UltiSnips"]):
            found = ulti_snips.find_all_snippet_directories()
        self.assertEqual(found, [str(d) for d in self.with_snippets])

    def test_literal_entries_do_not_list_any_directory(self):
        # Regression test for #1694: every entry used to be globbed from the
        # filesystem root, which on Python 3.12 listed "/", "/home", ... once
        # per runtimepath entry. A literal entry only needs an existence check.
        with _vim_config(self.plugins, ["UltiSnips"]), _recording_scandir() as listed:
            ulti_snips.find_all_snippet_directories()
        self.assertEqual(listed, [])

    def test_wildcard_entry_is_expanded(self):
        with _vim_config([self.bundle / "*"], ["UltiSnips"]):
            found = ulti_snips.find_all_snippet_directories()
        self.assertEqual(sorted(found), [str(d) for d in self.with_snippets])

    def test_wildcard_entry_only_lists_directories_below_the_wildcard(self):
        # Python 3.13+ binds `os.scandir` inside its globber at import time, so
        # nothing may get recorded there. What is recorded must stay inside the
        # globbed subtree on every version.
        with (
            _vim_config([self.bundle / "*"], ["UltiSnips"]),
            _recording_scandir() as listed,
        ):
            ulti_snips.find_all_snippet_directories()
        for directory in listed:
            self.assertTrue(directory.startswith(str(self.bundle)), directory)

    def test_several_directory_names_keep_runtimepath_order(self):
        (self.plugins[1] / "mine").mkdir()
        with _vim_config(self.plugins, ["UltiSnips", "mine"]):
            found = ulti_snips.find_all_snippet_directories()
        self.assertEqual(
            found,
            [
                str(self.plugins[0] / "UltiSnips"),
                str(self.plugins[1] / "mine"),
                str(self.plugins[2] / "UltiSnips"),
                str(self.plugins[4] / "UltiSnips"),
            ],
        )

    def test_single_absolute_directory_is_returned_unchecked(self):
        missing = self.root / "does_not_exist"
        with _vim_config(self.plugins, [str(missing)]):
            found = ulti_snips.find_all_snippet_directories()
        self.assertEqual(found, [str(missing)])

    def test_snippets_directory_name_is_rejected(self):
        with _vim_config(self.plugins, ["snippets"]), self.assertRaises(PebkacError):
            ulti_snips.find_all_snippet_directories()

    @unittest.skipIf(
        os.name != "posix" or os.geteuid() == 0,
        "needs POSIX directory permissions that apply to the current user",
    )
    def test_entry_below_unlistable_directory_is_found(self):
        # Traversable but not listable ancestors (e.g. a `/home` with mode
        # 0711) must not hide the snippet directory. Listing such a directory
        # raises PermissionError, which `Path.glob` swallows silently.
        locked = self.root / "locked"
        directory = locked / "plugin" / "UltiSnips"
        directory.mkdir(parents=True)
        locked.chmod(0o311)
        self.addCleanup(locked.chmod, 0o755)
        with _vim_config([locked / "plugin"], ["UltiSnips"]):
            found = ulti_snips.find_all_snippet_directories()
        self.assertEqual(found, [str(directory)])


@contextlib.contextmanager
def _snipmate_runtimepath(runtimepath):
    """Answers the `vim_helper.eval` query `_snipmate_files_for` makes as if
    Vim had the given 'runtimepath'."""
    answers = {"&runtimepath": ",".join(str(entry) for entry in runtimepath)}
    with mock.patch.object(
        snipmate.vim_helper, "eval", side_effect=answers.__getitem__
    ):
        yield


class TestSnipMateFilesFor(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="UltiSnipsTest_snipmate")
        self.addCleanup(tmp.cleanup)
        self.bundle = Path(tmp.name) / "bundle"
        self.plugins = [self.bundle / f"plugin{i}" for i in range(3)]
        for plugin in self.plugins:
            plugin.mkdir(parents=True)
        # Only the middle plugin ships snipMate snippets.
        self.snippet_file = self.plugins[1] / "snippets" / "python.snippets"
        self.snippet_file.parent.mkdir()
        self.snippet_file.write_text("snippet hi\n\thello\n")

    def test_literal_entries_find_snippet_files(self):
        with _snipmate_runtimepath(self.plugins):
            found = snipmate._snipmate_files_for("python")
        self.assertEqual(found, {str(self.snippet_file.resolve())})

    def test_wildcard_entry_is_expanded(self):
        with _snipmate_runtimepath([self.bundle / "*"]):
            found = snipmate._snipmate_files_for("python")
        self.assertEqual(found, {str(self.snippet_file.resolve())})

    def test_entries_without_snippets_directory_list_nothing(self):
        with (
            _snipmate_runtimepath([self.plugins[0], self.plugins[2]]),
            _recording_scandir() as listed,
        ):
            found = snipmate._snipmate_files_for("python")
        self.assertEqual(found, set())
        self.assertEqual(listed, [])


if __name__ == "__main__":
    unittest.main()
