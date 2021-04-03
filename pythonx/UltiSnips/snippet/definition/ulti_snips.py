#!/usr/bin/env python3
# encoding: utf-8

"""A UltiSnips snippet after parsing."""

from UltiSnips.snippet.definition.base import SnippetDefinition
from UltiSnips.snippet.parsing.ulti_snips import parse_and_instantiate


class UltiSnipsSnippetDefinition(SnippetDefinition):

    """See module doc."""

    def instantiate(self, snippet_instance, initial_text, indent):
        return parse_and_instantiate(snippet_instance, initial_text, indent)
