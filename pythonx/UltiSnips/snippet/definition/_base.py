#!/usr/bin/env python
# encoding: utf-8

"""Snippet representation after parsing."""

import re

from UltiSnips import _vim
from UltiSnips.compatibility import as_unicode
from UltiSnips.indent_util import IndentUtil
from UltiSnips.text import escape
from UltiSnips.text_objects import SnippetInstance

def _words_for_line(trigger, before, num_words=None):
    """ Gets the final 'num_words' words from 'before'.
    If num_words is None, then use the number of words in
    'trigger'.
    """
    if not len(before):
        return ''

    if num_words is None:
        num_words = len(trigger.split())

    word_list = before.split()
    if len(word_list) <= num_words:
        return before.strip()
    else:
        before_words = before
        for i in range(-1, -(num_words + 1), -1):
            left = before_words.rfind(word_list[i])
            before_words = before_words[:left]
        return before[len(before_words):].strip()

class SnippetDefinition(object):
    """Represents a snippet as parsed from a file."""

    _INDENT = re.compile(r"^[ \t]*")
    _TABS = re.compile(r"^\t*")

    def __init__(self, priority, trigger, value, description,
            options, globals, location):
        self._priority = priority
        self._trigger = as_unicode(trigger)
        self._value = as_unicode(value)
        self._description = as_unicode(description)
        self._opts = options
        self._matched = ""
        self._last_re = None
        self._globals = globals
        self._location = location

        # Make sure that we actually match our trigger in case we are
        # immediately expanded.
        self.matches(self._trigger)

    def __repr__(self):
        return "_SnippetDefinition(%r,%s,%s,%s)" % (
                self._priority, self._trigger, self._description, self._opts)

    def _re_match(self, trigger):
        """ Test if a the current regex trigger matches
        `trigger`. If so, set _last_re and _matched.
        """
        for match in re.finditer(self._trigger, trigger):
            if match.end() != len(trigger):
                continue
            else:
                self._matched = trigger[match.start():match.end()]

            self._last_re = match
            return match
        return False

    def has_option(self, opt):
        """ Check if the named option is set """
        return opt in self._opts

    @property
    def description(self):
        """Descriptive text for this snippet."""
        return ("(%s) %s" % (self._trigger, self._description)).strip()

    @property
    def priority(self):
        """The snippets priority, which defines which snippet will be preferred
        over others with the same trigger."""
        return self._priority

    @property
    def trigger(self):
        """The trigger text for the snippet."""
        return self._trigger

    @property
    def matched(self):
        """The last text that matched this snippet in match() or
        could_match()."""
        return self._matched

    @property
    def location(self):
        """Where this snippet was defined."""
        return self._location

    def matches(self, trigger):
        """Returns True if this snippet matches 'trigger'."""
        # If user supplies both "w" and "i", it should perhaps be an
        # error, but if permitted it seems that "w" should take precedence
        # (since matching at word boundary and within a word == matching at word
        # boundary).
        self._matched = ""

        # Don't expand on whitespace
        if trigger and trigger.rstrip() != trigger:
            return False

        words = _words_for_line(self._trigger, trigger)

        if "r" in self._opts:
            match = self._re_match(trigger)
        elif "w" in self._opts:
            words_len = len(self._trigger)
            words_prefix = words[:-words_len]
            words_suffix = words[-words_len:]
            match = (words_suffix == self._trigger)
            if match and words_prefix:
                # Require a word boundary between prefix and suffix.
                boundary_chars = escape(words_prefix[-1:] + \
                        words_suffix[:1], r'\"')
                match = _vim.eval('"%s" =~# "\\\\v.<."' % boundary_chars) != '0'
        elif "i" in self._opts:
            match = words.endswith(self._trigger)
        else:
            match = (words == self._trigger)

        # By default, we match the whole trigger
        if match and not self._matched:
            self._matched = self._trigger

        # Ensure the match was on a word boundry if needed
        if "b" in self._opts and match:
            text_before = trigger.rstrip()[:-len(self._matched)]
            if text_before.strip(" \t") != '':
                self._matched = ""
                return False
        return match

    def could_match(self, trigger):
        """Return True if this snippet could match the (partial) 'trigger'."""
        self._matched = ""

        # List all on whitespace.
        if trigger and trigger[-1] in (" ", "\t"):
            trigger = ""
        if trigger and trigger.rstrip() is not trigger:
            return False

        words = _words_for_line(self._trigger, trigger)

        if "r" in self._opts:
            # Test for full match only
            match = self._re_match(trigger)
        elif "w" in self._opts:
            # Trim non-empty prefix up to word boundary, if present.
            qwords = escape(words, r'\"')
            words_suffix = _vim.eval(
                    'substitute("%s", "\\\\v^.+<(.+)", "\\\\1", "")' % qwords)
            match = self._trigger.startswith(words_suffix)
            self._matched = words_suffix

            # TODO: list_snippets() function cannot handle partial-trigger
            # matches yet, so for now fail if we trimmed the prefix.
            if words_suffix != words:
                match = False
        elif "i" in self._opts:
            # TODO: It is hard to define when a inword snippet could match,
            # therefore we check only for full-word trigger.
            match = self._trigger.startswith(words)
        else:
            match = self._trigger.startswith(words)

        # By default, we match the words from the trigger
        if match and not self._matched:
            self._matched = words

        # Ensure the match was on a word boundry if needed
        if "b" in self._opts and match:
            text_before = trigger.rstrip()[:-len(self._matched)]
            if text_before.strip(" \t") != '':
                self._matched = ""
                return False

        return match

    def instantiate(self, snippet_instance, initial_text, indent):
        """Parses the content of this snippet and brings the corresponding text
        objects alive inside of Vim."""
        raise NotImplementedError()

    def launch(self, text_before, visual_content, parent, start, end):
        """Launch this snippet, overwriting the text 'start' to 'end' and
        keeping the 'text_before' on the launch line. 'Parent' is the parent
        snippet instance if any."""
        indent = self._INDENT.match(text_before).group(0)
        lines = (self._value + "\n").splitlines()
        ind_util = IndentUtil()

        # Replace leading tabs in the snippet definition via proper indenting
        initial_text = []
        for line_num, line in enumerate(lines):
            if "t" in self._opts:
                tabs = 0
            else:
                tabs = len(self._TABS.match(line).group(0))
            line_ind = ind_util.ntabs_to_proper_indent(tabs)
            if line_num != 0:
                line_ind = indent + line_ind

            initial_text.append(line_ind + line[tabs:])
        initial_text = '\n'.join(initial_text)

        snippet_instance = SnippetInstance(
                self, parent, initial_text, start, end, visual_content,
                last_re=self._last_re, globals=self._globals)
        self.instantiate(snippet_instance, initial_text, indent)

        snippet_instance.update_textobjects()
        return snippet_instance
