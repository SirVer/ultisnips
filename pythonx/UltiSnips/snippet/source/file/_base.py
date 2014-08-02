#!/usr/bin/env python
# encoding: utf-8

"""Code to provide access to UltiSnips files from disk."""

from collections import defaultdict
import hashlib
import os

from UltiSnips import _vim
from UltiSnips import compatibility
from UltiSnips.snippet.source._base import SnippetSource

def _hash_file(path):
    """Returns a hashdigest of 'path'"""
    if not os.path.isfile(path):
        return False
    return hashlib.sha1(open(path, "rb").read()).hexdigest()

class SnippetSyntaxError(RuntimeError):
    """Thrown when a syntax error is found in a file."""
    def __init__(self, filename, line_index, msg):
        RuntimeError.__init__(self, "%s in %s:%d" % (
            msg, filename, line_index))

class SnippetFileSource(SnippetSource):
    """Base class that abstracts away 'extends' info and file hashes."""

    def __init__(self):
        SnippetSource.__init__(self)
        self._files_for_ft = defaultdict(set)
        self._file_hashes = defaultdict(lambda: None)

    def ensure(self, filetypes):
        for ft in self.get_deep_extends(filetypes):
            if self._needs_update(ft):
                self._load_snippets_for(ft)

    def _get_all_snippet_files_for(self, ft):
        """Returns a set of all files that define snippets for 'ft'."""
        raise NotImplementedError()

    def _parse_snippet_file(self, filedata, filename):
        """Parses 'filedata' as a snippet file and yields events."""
        raise NotImplementedError()

    def _needs_update(self, ft):
        """Returns true if any files for 'ft' have changed and must be
        reloaded."""
        existing_files = self._get_all_snippet_files_for(ft)
        if existing_files != self._files_for_ft[ft]:
            self._files_for_ft[ft] = existing_files
            return True

        for filename in self._files_for_ft[ft]:
            if _hash_file(filename) != self._file_hashes[filename]:
                return True

        return False

    def _load_snippets_for(self, ft):
        """Load all snippets for the given 'ft'."""
        if ft in self._snippets:
            del self._snippets[ft]
            del self._extends[ft]
        for fn in self._files_for_ft[ft]:
            self._parse_snippets(ft, fn)
        # Now load for the parents
        for parent_ft in self.get_deep_extends([ft]):
            if parent_ft != ft and self._needs_update(parent_ft):
                self._load_snippets_for(parent_ft)

    def _parse_snippets(self, ft, filename):
        """Parse the 'filename' for the given 'ft' and watch it for changes in
        the future."""
        self._file_hashes[filename] = _hash_file(filename)
        file_data = compatibility.open_ascii_file(filename, "r").read()
        for event, data in self._parse_snippet_file(file_data, filename):
            if event == "error":
                msg, line_index = data
                filename = _vim.eval("""fnamemodify(%s, ":~:.")""" %
                        _vim.escape(filename))
                raise SnippetSyntaxError(filename, line_index, msg)
            elif event == "clearsnippets":
                priority, triggers = data
                self._snippets[ft].clear_snippets(priority, triggers)
            elif event == "extends":
                # TODO(sirver): extends information is more global
                # than one snippet source.
                filetypes, = data
                self.update_extends(ft, filetypes)
            elif event == "snippet":
                snippet, = data
                self._snippets[ft].add_snippet(snippet)
            else:
                assert False, "Unhandled %s: %r" % (event, data)
