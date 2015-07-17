#!/usr/bin/env python
# encoding: utf-8

"""Snippet representation after parsing."""

import re

import vim

from UltiSnips import _vim
from UltiSnips.compatibility import as_unicode
from UltiSnips.indent_util import IndentUtil
from UltiSnips.text import escape
from UltiSnips.text_objects import SnippetInstance
from UltiSnips.position import Position
from UltiSnips.buffer_helper import VimBufferHelper

__WHITESPACE_SPLIT = re.compile(r"\s")
def split_at_whitespace(string):
    """Like string.split(), but keeps empty words as empty words."""
    return re.split(__WHITESPACE_SPLIT, string)

def _words_for_line(trigger, before, num_words=None):
    """Gets the final 'num_words' words from 'before'.

    If num_words is None, then use the number of words in 'trigger'.

    """
    if num_words is None:
        num_words = len(split_at_whitespace(trigger))

    word_list = split_at_whitespace(before)
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
                 options, globals, location, context, actions):
        self._priority = int(priority)
        self._trigger = as_unicode(trigger)
        self._value = as_unicode(value)
        self._description = as_unicode(description)
        self._opts = options
        self._matched = ''
        self._last_re = None
        self._globals = globals
        self._location = location
        self._context_code = context
        self._context = None
        self._actions = actions

        # Make sure that we actually match our trigger in case we are
        # immediately expanded.
        self.matches(self._trigger)

    def __repr__(self):
        return '_SnippetDefinition(%r,%s,%s,%s)' % (
            self._priority, self._trigger, self._description, self._opts)

    def _re_match(self, trigger):
        """Test if a the current regex trigger matches `trigger`.

        If so, set _last_re and _matched.

        """
        for match in re.finditer(self._trigger, trigger):
            if match.end() != len(trigger):
                continue
            else:
                self._matched = trigger[match.start():match.end()]

            self._last_re = match
            return match
        return False

    def _context_match(self):
        # skip on empty buffer
        if len(vim.current.buffer) == 1 and vim.current.buffer[0] == "":
            return

        return self._eval_code('holder["result"] = ' + self._context_code)

    def _eval_code(self, code, additional_locals={}):
        code = "\n".join([
            'import re, os, vim, string, random',
            '\n'.join(self._globals.get('!p', [])).replace('\r\n', '\n'),
            code
        ])

        current = vim.current

        holder = {'result': False}

        locals = {
            'holder': holder,
            'window': current.window,
            'buffer': current.buffer,
            'line': current.window.cursor[0]-1,
            'column': current.window.cursor[1]-1,
            'cursor': (current.window.cursor[0]-1, current.window.cursor[1]-1)
        }

        locals.update(additional_locals)

        exec(code, locals)

        return holder["result"]

    def _execute_action(
        self,
        action,
        context,
        additional_locals={}
    ):
        mark_to_use = '`'
        mark_pos = _vim.get_mark_pos(mark_to_use)

        _vim.set_mark_from_pos(mark_to_use, _vim.get_cursor_pos())

        cursor_line_before = _vim.buf.line_till_cursor

        locals = {
            'new_cursor': None,
            'context': context,
        }

        locals.update(additional_locals)

        new_cursor, new_context = self._eval_code(
            action + "\nholder['result'] = (new_cursor, context)",
            locals
        )

        cursor_set_in_action = False
        if new_cursor:
            if new_cursor != 'keep':
                vim.current.window.cursor = (new_cursor[0]+1, new_cursor[1])
            cursor_set_in_action = True
        else:
            new_mark_pos = _vim.get_mark_pos(mark_to_use)

            cursor_invalid = False

            if _vim._is_pos_zero(new_mark_pos):
                cursor_invalid = True
            else:
                _vim.set_cursor_from_pos(new_mark_pos)
                if cursor_line_before != _vim.buf.line_till_cursor:
                    cursor_invalid = True

            if cursor_invalid:
                raise RuntimeError(
                    'line under the cursor was modified, but "new_cursor" ' +
                    'variable is not set; either set set "new_cursor" to ' +
                    'new cursor position, or do not modify cursor line'
                )

            # restore original mark position
            if _vim._is_pos_zero(mark_pos):
                _vim.delete_mark(mark_to_use)
            else:
                _vim.set_mark_from_pos(mark_to_use, mark_pos)
        return cursor_set_in_action, new_context

    def has_option(self, opt):
        """Check if the named option is set."""
        return opt in self._opts

    @property
    def description(self):
        """Descriptive text for this snippet."""
        return ('(%s) %s' % (self._trigger, self._description)).strip()

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

    @property
    def context(self):
        """The matched context."""
        return self._context

    def matches(self, before):
        """Returns True if this snippet matches 'before'."""
        # If user supplies both "w" and "i", it should perhaps be an
        # error, but if permitted it seems that "w" should take precedence
        # (since matching at word boundary and within a word == matching at word
        # boundary).
        self._matched = ''

        words = _words_for_line(self._trigger, before)

        if 'r' in self._opts:
            match = self._re_match(before)
        elif 'w' in self._opts:
            words_len = len(self._trigger)
            words_prefix = words[:-words_len]
            words_suffix = words[-words_len:]
            match = (words_suffix == self._trigger)
            if match and words_prefix:
                # Require a word boundary between prefix and suffix.
                boundary_chars = escape(words_prefix[-1:] +
                                        words_suffix[:1], r'\"')
                match = _vim.eval(
                    '"%s" =~# "\\\\v.<."' %
                    boundary_chars) != '0'
        elif 'i' in self._opts:
            match = words.endswith(self._trigger)
        else:
            match = (words == self._trigger)

        # By default, we match the whole trigger
        if match and not self._matched:
            self._matched = self._trigger

        # Ensure the match was on a word boundry if needed
        if 'b' in self._opts and match:
            text_before = before.rstrip()[:-len(self._matched)]
            if text_before.strip(' \t') != '':
                self._matched = ''
                return False

        if match and self._context_code:
            self._context = self._context_match()
            if not self.context:
                match = False

        return match

    def could_match(self, before):
        """Return True if this snippet could match the (partial) 'before'."""
        self._matched = ''

        # List all on whitespace.
        if before and before[-1] in (' ', '\t'):
            before = ''
        if before and before.rstrip() is not before:
            return False

        words = _words_for_line(self._trigger, before)

        if 'r' in self._opts:
            # Test for full match only
            match = self._re_match(before)
        elif 'w' in self._opts:
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
        elif 'i' in self._opts:
            # TODO: It is hard to define when a inword snippet could match,
            # therefore we check only for full-word trigger.
            match = self._trigger.startswith(words)
        else:
            match = self._trigger.startswith(words)

        # By default, we match the words from the trigger
        if match and not self._matched:
            self._matched = words

        # Ensure the match was on a word boundry if needed
        if 'b' in self._opts and match:
            text_before = before.rstrip()[:-len(self._matched)]
            if text_before.strip(' \t') != '':
                self._matched = ''
                return False

        return match

    def instantiate(self, snippet_instance, initial_text, indent):
        """Parses the content of this snippet and brings the corresponding text
        objects alive inside of Vim."""
        raise NotImplementedError()

    def do_pre_expand(self, visual_content, snippets_stack):
        buffer = VimBufferHelper(snippets_stack)
        if 'pre_expand' in self._actions:
            locals = {'buffer': buffer, 'visual_content': visual_content}

            cursor_set_in_action, new_context = self._execute_action(
                self._actions['pre_expand'], self._context, locals
            )

            self._context = new_context

            return buffer, cursor_set_in_action
        else:
            return buffer, False

    def do_post_expand(self, start, end, snippets_stack):
        buffer = VimBufferHelper(snippets_stack)
        if 'post_expand' in self._actions:
            locals = {
                'snippet_start': start,
                'snippet_end': end,
                'buffer': buffer
            }

            cursor_set_in_action, new_context = self._execute_action(
                self._actions['post_expand'], snippets_stack[0].context, locals
            )

            snippets_stack[0].context = new_context

            return buffer, cursor_set_in_action
        else:
            return buffer, False

    def do_post_jump(
        self, tabstop_number, jump_direction, snippets_stack
    ):
        buffer = VimBufferHelper(snippets_stack)
        if 'post_jump' in self._actions:
            start = snippets_stack[0].start
            end = snippets_stack[0].end
            locals = {
                'tabstop': tabstop_number,
                'jump_direction': jump_direction,
                'tabstops': snippets_stack[0].get_tabstops(),
                'snippet_start': start,
                'snippet_end': end,
                'buffer': buffer
            }

            cursor_set_in_action, new_context = self._execute_action(
                self._actions['post_jump'], snippets_stack[0].context, locals
            )

            snippets_stack[0].context = new_context

            return buffer, cursor_set_in_action
        else:
            return buffer, (False, None)


    def launch(self, text_before, visual_content, parent, start, end):
        """Launch this snippet, overwriting the text 'start' to 'end' and
        keeping the 'text_before' on the launch line.

        'Parent' is the parent snippet instance if any.

        """
        indent = self._INDENT.match(text_before).group(0)
        lines = (self._value + '\n').splitlines()
        ind_util = IndentUtil()

        # Replace leading tabs in the snippet definition via proper indenting
        initial_text = []
        for line_num, line in enumerate(lines):
            if 't' in self._opts:
                tabs = 0
            else:
                tabs = len(self._TABS.match(line).group(0))
            line_ind = ind_util.ntabs_to_proper_indent(tabs)
            if line_num != 0:
                line_ind = indent + line_ind

            result_line = line_ind + line[tabs:]
            if 'm' in self._opts:
                result_line = result_line.rstrip()
            initial_text.append(result_line)
        initial_text = '\n'.join(initial_text)

        snippet_instance = SnippetInstance(
            self, parent, initial_text, start, end, visual_content,
            last_re=self._last_re, globals=self._globals,
            context=self._context)
        self.instantiate(snippet_instance, initial_text, indent)

        snippet_instance.update_textobjects()
        return snippet_instance
