#!/usr/bin/env python
# encoding: utf-8

"""Handles manually added snippets UltiSnips_Manager.add_snippet()."""

from UltiSnips.snippet.source._base import SnippetSource

class AddedSnippetsSource(SnippetSource):
    """See module docstring."""

    def add_snippet(self, ft, snippet):
        """Adds the given 'snippet' for 'ft'."""
        self._snippets[ft].add_snippet(snippet)
