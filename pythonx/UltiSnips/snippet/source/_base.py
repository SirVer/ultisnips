#!/usr/bin/env python
# encoding: utf-8

"""Base class for snippet sources."""

from collections import defaultdict

from UltiSnips.snippet.source._snippet_dictionary import SnippetDictionary

class SnippetSource(object):
    """See module docstring."""

    def __init__(self):
        self._snippets = defaultdict(SnippetDictionary)

    def get_snippets(self, filetypes, before, possible):
        """Returns the snippets for all 'filetypes' (in order) and their parents
        matching the text 'before'. If 'possible' is true, a partial match is
        enough. Base classes can override this method to provide means of
        creating snippets on the fly.

        Returns a list of SnippetDefinition s.
        """
        found_snippets = []
        for ft in filetypes:
            found_snippets += self._find_snippets(ft, before, possible)
        return found_snippets

    def _find_snippets(self, ft, trigger, potentially=False, seen=None):
        """Find snippets matching 'trigger' for 'ft'. If 'potentially' is True,
        partial matches are enough."""
        snips = self._snippets.get(ft, None)
        if not snips:
            return []
        if not seen:
            seen = set()
        seen.add(ft)
        parent_results = []
        # TODO(sirver): extends information is not bound to one
        # source. It should be tracked further up.
        for parent_ft in snips.extends:
            if parent_ft not in seen:
                seen.add(parent_ft)
                parent_results += self._find_snippets(parent_ft, trigger,
                        potentially, seen)
        return parent_results + snips.get_matching_snippets(
            trigger, potentially)
