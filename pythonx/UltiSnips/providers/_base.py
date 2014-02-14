#!/usr/bin/env python
# encoding: utf-8

"""Base class for snippet providers."""

from collections import defaultdict

from UltiSnips.providers._snippet_dictionary import SnippetDictionary

class SnippetProvider(object):
    """See module docstring."""

    def __init__(self):
        self._snippets = defaultdict(SnippetDictionary)

    def get_snippets(self, filetypes, before, possible):
        """Returns the snippets for all 'filetypes' (in order) and their
        parents matching the text 'before'. If 'possible' is true, a partial
        match is enough."""
        found_snippets = []
        for ft in filetypes:
            found_snippets += self._find_snippets(ft, before, possible)

        # Search if any of the snippets overwrites the previous
        # Dictionary allows O(1) access for easy overwrites
        snippets = {}
        for snip in found_snippets:
            if (snip.trigger not in snippets) or snip.overwrites_previous:
                snippets[snip.trigger] = []
            snippets[snip.trigger].append(snip)

        # Transform dictionary into flat list of snippets
        selected_snippets = set(
                [item for sublist in snippets.values() for item in sublist])
        # Return snippets to their original order
        snippets = [snip for snip in found_snippets if
                snip in selected_snippets]

        return snippets

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
        # provider. It should be tracked further up.
        for parent_ft in snips.extends:
            if parent_ft not in seen:
                seen.add(parent_ft)
                parent_results += self._find_snippets(parent_ft, trigger,
                        potentially, seen)
        return parent_results + snips.get_matching_snippets(
            trigger, potentially)
