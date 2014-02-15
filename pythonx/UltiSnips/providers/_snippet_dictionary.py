#!/usr/bin/env python
# encoding: utf-8

"""Implements a container for parsed snippets."""

import hashlib
import os

def _hash_file(path):
    """Returns a hashdigest of 'path'"""
    if not os.path.isfile(path):
        return False
    return hashlib.sha1(open(path, "rb").read()).hexdigest()

# TODO(sirver): This class should not hash any files nor keep track of extends.
class SnippetDictionary(object):
    """See module docstring."""

    def __init__(self):
        self._added = []
        self._extends = []
        self._files = {}
        self._snippets = []

    def add_snippet(self, snippet, filename):
        """Add 'snippet' to this dictionary. If 'filename' is given, also watch
        the original file for changes."""
        if filename:
            self._snippets.append(snippet)
            if filename not in self.files:
                self.addfile(filename)
        else:
            self._added.append(snippet)

    def get_matching_snippets(self, trigger, potentially):
        """Returns all snippets matching the given trigger. If 'potentially' is
        true, returns all that could_match()."""
        all_snippets = self._added + self._snippets
        if not potentially:
            return [s for s in all_snippets if s.matches(trigger)]
        else:
            return [s for s in all_snippets if s.could_match(trigger)]

    def clear_snippets(self, triggers=None):
        """Remove all snippets that match each trigger in 'triggers'. When
        'triggers' is None, empties this dictionary completely."""
        if triggers is None:
            triggers = []
        if triggers:
            for trigger in triggers:
                for snippet in self.get_matching_snippets(trigger, False):
                    if snippet in self._snippets:
                        self._snippets.remove(snippet)
                    if snippet in self._added:
                        self._added.remove(snippet)
        else:
            self._snippets = []
            self._added = []

    def addfile(self, path):
        """Add this file to the files we read triggers from."""
        self.files[path] = _hash_file(path)

    def has_any_file_changed(self):
        """Returns True if any of our watched files has changed since we read
        it last."""
        for path, hash in self.files.items():
            if not hash or hash != _hash_file(path):
                return True
        return False

    @property
    def files(self):
        """All files we have read snippets from."""
        return self._files

    @property
    def extends(self):
        """The list of filetypes this filetype extends."""
        return self._extends
