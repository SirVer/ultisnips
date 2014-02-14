#!/usr/bin/env python
# encoding: utf-8

"""Handles manually added snippets (i.e. not in a file)."""

from UltiSnips.providers._base import SnippetProvider

class AddedSnippetsProvider(SnippetProvider):
    """See module docstring."""

    # TODO(sirver): filename makes no sense here. Is it even used?
    def add_snippet(self, ft, snippet, filename):
        """Adds the given 'snippet' for 'ft'."""
        self._snippets[ft].add_snippet(snippet, filename)
