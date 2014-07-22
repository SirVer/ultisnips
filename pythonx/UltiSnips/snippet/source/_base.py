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
        pass

    def get_snippets(self, filetypes, before, possible):
        """Returns the snippets for all 'filetypes' (in order) and their parents
        matching the text 'before'. If 'possible' is true, a partial match is
        enough. Base classes can override this method to provide means of
        creating snippets on the fly.

        Returns a list of SnippetDefinition s.
        """
        def __inner(fts):
            result = []
            existing_fts = filter(lambda ft: ft in self._snippets, fts)
            for ft in existing_fts:
                snips = self._snippets[ft]
                result.extend(snips.get_matching_snippets(before, possible))
            return result
        return __inner(self.get_deep_extends(filetypes))

    def get_clear_priority(self, filetypes):
        def __inner(fts):
            pri = None
            existing_fts = filter(lambda ft: ft in self._snippets, fts)
            for ft in existing_fts:
                snippets = self._snippets[ft]
                if pri is None or snippets._clear_priority > pri:
                    pri = snippets._clear_priority
            return pri
        return __inner(self.get_deep_extends(filetypes))

    def get_cleared(self, filetypes):
        def __inner(fts):
            cleared = {}
            existing_fts = filter(lambda ft: ft in self._snippets, fts)
            for ft in existing_fts:
                snippets = self._snippets[ft]
                for key, value in snippets._cleared.items():
                    if key not in cleared or value > cleared[key]:
                        cleared[key] = value
            return cleared
        return __inner(self.get_deep_extends(filetypes))

    def update_extends(self, child_ft, parent_fts):
        self._extends[child_ft].update(parent_fts)

    def get_deep_extends(self, root_filetypes):
        seen = set(root_filetypes)
        l = list(set(root_filetypes))
        while l:
            top = l.pop()
            for ft in self._extends[top]:
                if ft not in seen:
                    seen.add(ft)
                    l.append(ft)
        return seen
