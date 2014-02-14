#!/usr/bin/env python
# encoding: utf-8

"""Sources of snippet definitions."""

# TODO(sirver): these should register themselves with the Manager, so that
# other plugins can extend them more easily.
from UltiSnips.providers.snippet_file import UltiSnipsFileProvider, \
    base_snippet_files_for
from UltiSnips.providers.added_snippets_provider import AddedSnippetsProvider
