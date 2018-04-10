#!/usr/bin/env python
# encoding: utf-8

"""Base class for snippet sources."""

from collections import defaultdict

from UltiSnips.snippet.source._snippet_dictionary import SnippetDictionary


class SnippetSource(object):

    """See module docstring."""

    def __init__(self):
        self._snippets = defaultdict(SnippetDictionary)
        self._extends = defaultdict(set)

    def ensure(self, filetypes):
        """Ensures that snippets are loaded."""

    def refresh(self):
        """Resets all snippets, so that they are reloaded on the next call to
        ensure.
        """

    def _get_existing_deep_extends(self, base_filetypes):
        """Helper for get all existing filetypes extended by base filetypes."""
        deep_extends = self.get_deep_extends(base_filetypes)
        return [ft for ft in deep_extends if ft in self._snippets]

    def get_snippets(self, filetypes, before, possible, autotrigger_only,
            visual_content):
        """Returns the snippets for all 'filetypes' (in order) and their
        parents matching the text 'before'. If 'possible' is true, a partial
        match is enough. Base classes can override this method to provide means
        of creating snippets on the fly.

        Returns a list of SnippetDefinition s.

        """
        result = []
        for ft in self._get_existing_deep_extends(filetypes):
            snips = self._snippets[ft]
            result.extend(snips.get_matching_snippets(before, possible,
                                                      autotrigger_only,
                                                      visual_content))
        return result

    def get_clear_priority(self, filetypes):
        """Get maximum clearsnippets priority without arguments for specified
        filetypes, if any.

        It returns None if there are no clearsnippets.

        """
        pri = None
        for ft in self._get_existing_deep_extends(filetypes):
            snippets = self._snippets[ft]
            if pri is None or snippets._clear_priority > pri:
                pri = snippets._clear_priority
        return pri

    def get_cleared(self, filetypes):
        """Get a set of cleared snippets marked by clearsnippets with arguments
        for specified filetypes."""
        cleared = {}
        for ft in self._get_existing_deep_extends(filetypes):
            snippets = self._snippets[ft]
            for key, value in snippets._cleared.items():
                if key not in cleared or value > cleared[key]:
                    cleared[key] = value
        return cleared

    def update_extends(self, child_ft, parent_fts):
        """Update the extending relation by given child filetype and its parent
        filetypes."""
        self._extends[child_ft].update(parent_fts)

    def get_deep_extends(self, base_filetypes):
        """Get a list of filetypes that is either directed or indirected
        extended by given base filetypes.

        Note that the returned list include the root filetype itself.

        """
        seen = set(base_filetypes)
        todo_fts = list(set(base_filetypes))
        while todo_fts:
            todo_ft = todo_fts.pop()
            unseen_extends = set(
                ft for ft in self._extends[todo_ft] if ft not in seen)
            seen.update(unseen_extends)
            todo_fts.extend(unseen_extends)
        return seen
