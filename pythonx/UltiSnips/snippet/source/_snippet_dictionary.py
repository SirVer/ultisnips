#!/usr/bin/env python
# encoding: utf-8

"""Implements a container for parsed snippets."""

class SnippetDictionary(object):

    """See module docstring."""

    def __init__(self):
        self._snippets = []
        self._cleared = {}
        self._clear_priority = float("-inf")

    def add_snippet(self, snippet):
        """Add 'snippet' to this dictionary."""
        self._snippets.append(snippet)

    def get_matching_snippets(self, trigger, potentially, autotrigger_only):
        """Returns all snippets matching the given trigger.

        If 'potentially' is true, returns all that could_match().

        If 'autotrigger_only' is true, function will return only snippets which
        are marked with flag 'A' (should be automatically expanded without
        trigger key press).
        It's handled specially to avoid walking down the list of all snippets,
        which can be very slow, because function will be called on each change
        made in insert mode.

        """
        all_snippets = self._snippets
        if autotrigger_only:
            all_snippets = [s for s in all_snippets if s.has_option('A')]

        if not potentially:
            return [s for s in all_snippets if s.matches(trigger)]
        else:
            return [s for s in all_snippets if s.could_match(trigger)]

    def clear_snippets(self, priority, triggers):
        """Clear the snippets by mark them as cleared.

        If trigger is None, it updates the value of clear priority
        instead.

        """
        if not triggers:
            if self._clear_priority is None or priority > self._clear_priority:
                self._clear_priority = priority
        else:
            for trigger in triggers:
                if (trigger not in self._cleared or
                        priority > self._cleared[trigger]):
                    self._cleared[trigger] = priority

    def __len__(self):
        return len(self._snippets)
