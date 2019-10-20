#!/usr/bin/env python
# encoding: utf-8

"""A snipMate snippet after parsing."""

from UltiSnips.snippet.definition.base import SnippetDefinition
from UltiSnips.snippet.parsing.snipmate import parse_and_instantiate


class SnipMateSnippetDefinition(SnippetDefinition):

    """See module doc."""

    SNIPMATE_SNIPPET_PRIORITY = -1000

    def __init__(self, trigger, value, description, location):
        SnippetDefinition.__init__(
            self,
            self.SNIPMATE_SNIPPET_PRIORITY,
            trigger,
            value,
            description,
            "",
            {},
            location,
            None,
            {},
        )

    def instantiate(self, snippet_instance, initial_text, indent):
        parse_and_instantiate(snippet_instance, initial_text, indent)
