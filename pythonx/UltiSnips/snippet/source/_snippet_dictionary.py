#!/usr/bin/env python
# encoding: utf-8

"""Implements a container for parsed snippets."""

# TODO(sirver): This class should not keep track of extends.
class SnippetDictionary(object):
    """See module docstring."""

    def __init__(self):
        self._snippets = []
        self._extends = []

    def add_snippet(self, snippet):
        """Add 'snippet' to this dictionary."""
        self._snippets.append(snippet)

    def get_matching_snippets(self, trigger, potentially):
        """Returns all snippets matching the given trigger. If 'potentially' is
        true, returns all that could_match()."""
        all_snippets = self._snippets
        if not potentially:
            return [s for s in all_snippets if s.matches(trigger)]
        else:
            return [s for s in all_snippets if s.could_match(trigger)]

    def clear_snippets(self, triggers):
        """Remove all snippets that match each trigger in 'triggers'. When
        'triggers' is None, empties this dictionary completely."""
        if not triggers:
            self._snippets = []
            return
        for trigger in triggers:
            for snippet in self.get_matching_snippets(trigger, False):
                if snippet in self._snippets:
                    self._snippets.remove(snippet)

    @property
    def extends(self):
        """The list of filetypes this filetype extends."""
        return self._extends
