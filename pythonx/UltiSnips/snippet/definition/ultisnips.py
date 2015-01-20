#!/usr/bin/env python
# encoding: utf-8

"""A UltiSnips snippet after parsing."""

from UltiSnips.snippet.definition._base import SnippetDefinition
from UltiSnips.snippet.parsing.ultisnips import parse_and_instantiate


class UltiSnipsSnippetDefinition(SnippetDefinition):

    """See module doc."""

    def instantiate(self, snippet_instance, initial_text, indent):
        return parse_and_instantiate(snippet_instance, initial_text, indent)
