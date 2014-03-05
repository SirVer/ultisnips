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

    def get_snippets(self, filetypes, before, possible):
        for ft in filetypes:
            self._ensure_loaded(ft, set())
        return SnippetSource.get_snippets(self, filetypes, before, possible)

    def _get_all_snippet_files_for(self, ft):
        """Returns a set of all files that define snippets for 'ft'."""
        raise NotImplementedError()

    def _parse_snippet_file(self, filedata, filename):
        """Parses 'filedata' as a snippet file and yields events."""
        raise NotImplementedError()

    def _ensure_loaded(self, ft, already_loaded):
        """Make sure that the snippets for 'ft' and everything it extends are
        loaded."""
        if ft in already_loaded:
            return
        already_loaded.add(ft)

        if self._needs_update(ft):
            self._load_snippets_for(ft)

        for parent in self._snippets[ft].extends:
            self._ensure_loaded(parent, already_loaded)

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
        for fn in self._files_for_ft[ft]:
            self._parse_snippets(ft, fn)
        # Now load for the parents
        for parent_ft in self._snippets[ft].extends:
            if parent_ft not in self._snippets:
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
                triggers, = data
                self._snippets[ft].clear_snippets(triggers)
            elif event == "extends":
                # TODO(sirver): extends information is more global
                # than one snippet source.
                filetypes, = data
                self._add_extending_info(ft, filetypes)
            elif event == "snippet":
                snippet, = data
                self._snippets[ft].add_snippet(snippet)
            else:
                assert False, "Unhandled %s: %r" % (event, data)

    def _add_extending_info(self, ft, parents):
        """Add the list of 'parents' as being extended by the 'ft'."""
        sd = self._snippets[ft]
        for parent in parents:
            if parent in sd.extends:
                continue
            sd.extends.append(parent)
