#!/usr/bin/env python
# encoding: utf-8

"""Sources of snippet definitions."""

# TODO(sirver): these should register themselves with the Manager, so that
# other plugins can extend them more easily.
from UltiSnips.snippet.source.added import AddedSnippetsSource
from UltiSnips.snippet.source.file.snipmate import SnipMateFileSource
from UltiSnips.snippet.source.file.ultisnips import UltiSnipsFileSource, \
    base_snippet_files_for
