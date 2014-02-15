#!/usr/bin/env python
# encoding: utf-8

"""Handles manually added snippets through UltiSnips#AddSnippet or
UltiSnips_Manager.add_snippet()."""

from UltiSnips.providers._base import SnippetProvider

class AddedSnippetsProvider(SnippetProvider):
    """See module docstring."""

    def add_snippet(self, ft, snippet):
        """Adds the given 'snippet' for 'ft'."""
        self._snippets[ft].add_snippet(snippet, None)
