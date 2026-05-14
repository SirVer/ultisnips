#!/usr/bin/env python3

"""Base class for snippet sources."""

from collections import defaultdict

from UltiSnips.snippet.source.snippet_dictionary import SnippetDictionary


class SnippetSource:
    """See module docstring."""

    def __init__(self):
        self._snippets = defaultdict(SnippetDictionary)
        # dict-with-None-values gives us a set that preserves insertion order,
        # which keeps `get_deep_extends` deterministic — see issue surfaced in
        # `DuplicateSnippets_DoesNotMergeDistinctTriggers`.
        self._extends = defaultdict(dict)

    def ensure(self, filetypes):
        """Ensures that snippets are loaded."""

    def refresh(self):
        """Resets all snippets, so that they are reloaded on the next call to
        ensure.
        """

    def get_all_snippet_files_for(self, ft):
        """Returns the set of on-disk snippet files this source would load
        for filetype 'ft'. Returns an empty set for sources that don't
        back snippets with files (added programmatically, dynamic
        sources, etc.). File-backed subclasses override this."""
        return set()

    def _get_existing_deep_extends(self, base_filetypes):
        """Helper for get all existing filetypes extended by base filetypes."""
        deep_extends = self.get_deep_extends(base_filetypes)
        return [ft for ft in deep_extends if ft in self._snippets]

    def get_snippets(
        self, filetypes, before, possible, autotrigger_only, visual_content
    ):
        """Returns the snippets for all 'filetypes' (in order) and their
        parents matching the text 'before'. If 'possible' is true, a partial
        match is enough. Base classes can override this method to provide means
        of creating snippets on the fly.

        Returns a list of SnippetDefinition s.

        """
        result = []
        for ft in self._get_existing_deep_extends(filetypes):
            snips = self._snippets[ft]
            result.extend(
                snips.get_matching_snippets(
                    before, possible, autotrigger_only, visual_content
                )
            )
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
        for ft in parent_fts:
            self._extends[child_ft][ft] = None

    def get_deep_extends(self, base_filetypes):
        """Return the list of filetypes that is directly or transitively
        extended by `base_filetypes`, including the base filetypes themselves.

        Iteration is BFS so base filetypes appear before their parents, and
        among siblings the order is the insertion order of the `extends`
        directives. A stable order matters: the "Multiple matches" prompt
        and per-trigger priority resolution both walk this list, so two
        Vim sessions must agree on which snippet is "first".
        """
        seen = {}  # dict gives us an order-preserving set
        for ft in base_filetypes:
            seen.setdefault(ft, None)
        todo_fts = list(seen)
        while todo_fts:
            todo_ft = todo_fts.pop(0)
            for parent_ft in self._extends[todo_ft]:
                if parent_ft not in seen:
                    seen[parent_ft] = None
                    todo_fts.append(parent_ft)
        return list(seen)
