#!/usr/bin/env python
# encoding: utf-8

"""Base class for snippet sources."""

from collections import defaultdict

from UltiSnips.snippet.source._snippet_dictionary import SnippetDictionary

class SnippetSource(object):
    """See module docstring."""

    def __init__(self):
        self._snippets = defaultdict(SnippetDictionary)

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
        return __inner(filetypes) + __inner(self._extends_all(filetypes))

    def get_clear_priority(self, filetypes):
        def __inner(fts):
            pri = None
            existing_fts = filter(lambda ft: ft in self._snippets, fts)
            for ft in existing_fts:
                snippets = self._snippets[ft]
                if pri is None or snippets._clear_priority > pri:
                    pri = snippets._clear_priority
            return pri
        priority = __inner(filetypes)
        deep_clear_priority = __inner(self._extends_all(filetypes))
        if deep_clear_priority is None:
            return priority
        elif priority is None:
            return deep_clear_priority
        else:
            return max(priority, deep_clear_priority)

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
        return dict(__inner(filetypes).items() + __inner(self._extends_all(filetypes)).items())

    def _extends_all(self, filetypes, seen=None):
        """Return deep extends dependency, excluding the filetype itself
        """
        if seen is None:
            seen = set(filetypes)

        shallow_extends = set()
        for filetype in filetypes:
            ft_extends = self._snippets[filetype].extends
            havnt_seen = set(filter(lambda ft: ft not in seen, ft_extends))
            seen.update(havnt_seen)
            shallow_extends.update(havnt_seen)
        if not shallow_extends:
            return shallow_extends
        return shallow_extends | self._extends_all(shallow_extends, seen)
