#!/usr/bin/env python
# encoding: utf-8

"""Code to provide access to UltiSnips files from disk."""

from collections import defaultdict
import os

from UltiSnips import vim_helper
from UltiSnips import compatibility
from UltiSnips.snippet.source.base import SnippetSource


class SnippetSyntaxError(RuntimeError):

    """Thrown when a syntax error is found in a file."""

    def __init__(self, filename, line_index, msg):
        RuntimeError.__init__(self, "%s in %s:%d" % (msg, filename, line_index))


class SnippetFileSource(SnippetSource):
    """Base class that abstracts away 'extends' info and file hashes."""

    def __init__(self):
        SnippetSource.__init__(self)

    def ensure(self, filetypes):
        for ft in self.get_deep_extends(filetypes):
            if self._needs_update(ft):
                self._load_snippets_for(ft)

    def refresh(self):
        self.__init__()

    def _get_all_snippet_files_for(self, ft):
        """Returns a set of all files that define snippets for 'ft'."""
        raise NotImplementedError()

    def _parse_snippet_file(self, filedata, filename):
        """Parses 'filedata' as a snippet file and yields events."""
        raise NotImplementedError()

    def _needs_update(self, ft):
        """Returns true if any files for 'ft' have changed and must be
        reloaded."""
        return not (ft in self._snippets)

    def _load_snippets_for(self, ft):
        """Load all snippets for the given 'ft'."""
        assert ft not in self._snippets
        for fn in self._get_all_snippet_files_for(ft):
            self._parse_snippets(ft, fn)
        # Now load for the parents
        for parent_ft in self.get_deep_extends([ft]):
            if parent_ft != ft and self._needs_update(parent_ft):
                self._load_snippets_for(parent_ft)

    def _parse_snippets(self, ft, filename):
        """Parse the 'filename' for the given 'ft'."""
        with open(filename, "r", encoding="utf-8") as to_read:
            file_data = to_read.read()
        self._snippets[ft]  # Make sure the dictionary exists
        for event, data in self._parse_snippet_file(file_data, filename):
            if event == "error":
                msg, line_index = data
                filename = vim_helper.eval(
                    """fnamemodify(%s, ":~:.")""" % vim_helper.escape(filename)
                )
                raise SnippetSyntaxError(filename, line_index, msg)
            elif event == "clearsnippets":
                priority, triggers = data
                self._snippets[ft].clear_snippets(priority, triggers)
            elif event == "extends":
                # TODO(sirver): extends information is more global
                # than one snippet source.
                (filetypes,) = data
                self.update_extends(ft, filetypes)
            elif event == "snippet":
                (snippet,) = data
                self._snippets[ft].add_snippet(snippet)
            else:
                assert False, "Unhandled %s: %r" % (event, data)
