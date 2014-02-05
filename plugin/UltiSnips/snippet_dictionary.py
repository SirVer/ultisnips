#!/usr/bin/env python
# encoding: utf-8

import hashlib
import os


def _hash_file(path):
    """Returns a hashdigest of 'path'"""
    if not os.path.isfile(path):
        return False
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


class SnippetDictionary(object):
    def __init__(self, *args, **kwargs):
        self._added = []
        self.reset()

    def reset(self):
        self._snippets = []
        self._extends = []
        self._files = {}

    def add_snippet(self, s, fn=None):
        if fn:
            self._snippets.append(s)

            if fn not in self.files:
                self.addfile(fn)
        else:
            self._added.append(s)

    def get_matching_snippets(self, trigger, potentially):
        """Returns all snippets matching the given trigger."""
        if not potentially:
            return [ s for s in self.snippets if s.matches(trigger) ]
        else:
            return [ s for s in self.snippets if s.could_match(trigger) ]

    @property
    def snippets(self):
        return self._added + self._snippets

    def clear_snippets(self, triggers=[]):
        """Remove all snippets that match each trigger in triggers.
            When triggers is empty, removes all snippets.
        """
        if triggers:
            for t in triggers:
                for s in self.get_matching_snippets(t, potentially=False):
                    if s in self._snippets:
                        self._snippets.remove(s)
                    if s in self._added:
                        self._added.remove(s)
        else:
            self._snippets = []
            self._added = []

    @property
    def files(self):
        return self._files

    def addfile(self, path):
        self.files[path] = _hash_file(path)

    def needs_update(self):
        for path, hash in self.files.items():
            if not hash or hash != _hash_file(path):
                return True
        return False

    def extends():
        def fget(self):
            return self._extends
        def fset(self, value):
            self._extends = value
        return locals()
    extends = property(**extends())
