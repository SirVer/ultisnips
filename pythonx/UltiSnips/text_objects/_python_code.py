#!/usr/bin/env python
# encoding: utf-8

"""Implements `!p ` interpolation."""

import os
from collections import namedtuple

from UltiSnips import _vim
from UltiSnips.compatibility import as_unicode
from UltiSnips.indent_util import IndentUtil
from UltiSnips.text_objects._base import NoneditableTextObject
from UltiSnips.vim_state import _Placeholder
import UltiSnips.snippet_manager


class _Tabs(object):

    """Allows access to tabstop content via t[] inside of python code."""

    def __init__(self, to):
        self._to = to

    def __getitem__(self, no):
        ts = self._to._get_tabstop(
            self._to,
            int(no))  # pylint:disable=protected-access
        if ts is None:
            return ''
        return ts.current_text

    def __setitem__(self, no, value):
        ts = self._to._get_tabstop(
            self._to,
            int(no))  # pylint:disable=protected-access
        if ts is None:
            return
        ts.overwrite(value)

_VisualContent = namedtuple('_VisualContent', ['mode', 'text'])


class SnippetUtilForAction(dict):
    def __init__(self, *args, **kwargs):
        super(SnippetUtilForAction, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def expand_anon(self, *args, **kwargs):
        UltiSnips.snippet_manager.UltiSnips_Manager.expand_anon(
            *args, **kwargs
        )
        self.cursor.preserve()


class SnippetUtilCursor(object):
    def __init__(self, cursor):
        self._cursor = [cursor[0] - 1, cursor[1]]
        self._set = False

    def preserve(self):
        self._set = True
        self._cursor = [
            _vim.buf.cursor[0],
            _vim.buf.cursor[1],
        ]

    def is_set(self):
        return self._set

    def set(self, line, column):
        self.__setitem__(0, line)
        self.__setitem__(1, column)

    def to_vim_cursor(self):
        return (self._cursor[0] + 1, self._cursor[1])

    def __getitem__(self, index):
        return self._cursor[index]

    def __setitem__(self, index, value):
        self._set = True
        self._cursor[index] = value

    def __len__(self):
        return 2

    def __str__(self):
        return str((self._cursor[0], self._cursor[1]))


class SnippetUtil(object):

    """Provides easy access to indentation, etc.

    This is the 'snip' object in python code.

    """

    def __init__(self, initial_indent, vmode, vtext, context, parent):
        self._ind = IndentUtil()
        self._visual = _VisualContent(vmode, vtext)
        self._initial_indent = self._ind.indent_to_spaces(initial_indent)
        self._reset('')
        self._context = context
        self._start = parent.start
        self._end = parent.end
        self._parent = parent

    def _reset(self, cur):
        """Gets the snippet ready for another update.

        :cur: the new value for c.

        """
        self._ind.reset()
        self._cur = cur
        self._rv = ''
        self._changed = False
        self.reset_indent()

    def shift(self, amount=1):
        """Shifts the indentation level. Note that this uses the shiftwidth
        because thats what code formatters use.

        :amount: the amount by which to shift.

        """
        self.indent += ' ' * self._ind.shiftwidth * amount

    def unshift(self, amount=1):
        """Unshift the indentation level. Note that this uses the shiftwidth
        because thats what code formatters use.

        :amount: the amount by which to unshift.

        """
        by = -self._ind.shiftwidth * amount
        try:
            self.indent = self.indent[:by]
        except IndexError:
            self.indent = ''

    def mkline(self, line='', indent=None):
        """Creates a properly set up line.

        :line: the text to add
        :indent: the indentation to have at the beginning
                 if None, it uses the default amount

        """
        if indent is None:
            indent = self.indent
            # this deals with the fact that the first line is
            # already properly indented
            if '\n' not in self._rv:
                try:
                    indent = indent[len(self._initial_indent):]
                except IndexError:
                    indent = ''
            indent = self._ind.spaces_to_indent(indent)

        return indent + line

    def reset_indent(self):
        """Clears the indentation."""
        self.indent = self._initial_indent

    # Utility methods
    @property
    def fn(self):  # pylint:disable=no-self-use,invalid-name
        """The filename."""
        return _vim.eval('expand("%:t")') or ''

    @property
    def basename(self):  # pylint:disable=no-self-use
        """The filename without extension."""
        return _vim.eval('expand("%:t:r")') or ''

    @property
    def ft(self):  # pylint:disable=invalid-name
        """The filetype."""
        return self.opt('&filetype', '')

    @property
    def rv(self):  # pylint:disable=invalid-name
        """The return value.

        The text to insert at the location of the placeholder.

        """
        return self._rv

    @rv.setter
    def rv(self, value):  # pylint:disable=invalid-name
        """See getter."""
        self._changed = True
        self._rv = value

    @property
    def _rv_changed(self):
        """True if rv has changed."""
        return self._changed

    @property
    def c(self):  # pylint:disable=invalid-name
        """The current text of the placeholder."""
        return self._cur

    @property
    def v(self):  # pylint:disable=invalid-name
        """Content of visual expansions."""
        return self._visual

    @property
    def p(self):
        if self._parent.current_placeholder:
            return self._parent.current_placeholder
        else:
            return _Placeholder('', 0, 0)

    @property
    def context(self):
        return self._context

    def opt(self, option, default=None):  # pylint:disable=no-self-use
        """Gets a Vim variable."""
        if _vim.eval("exists('%s')" % option) == '1':
            try:
                return _vim.eval(option)
            except _vim.error:
                pass
        return default

    def __add__(self, value):
        """Appends the given line to rv using mkline."""
        self.rv += '\n'  # pylint:disable=invalid-name
        self.rv += self.mkline(value)
        return self

    def __lshift__(self, other):
        """Same as unshift."""
        self.unshift(other)

    def __rshift__(self, other):
        """Same as shift."""
        self.shift(other)

    @property
    def snippet_start(self):
        """
        Returns start of the snippet in format (line, column).
        """
        return self._start

    @property
    def snippet_end(self):
        """
        Returns end of the snippet in format (line, column).
        """
        return self._end

    @property
    def buffer(self):
        return _vim.buf


class PythonCode(NoneditableTextObject):

    """See module docstring."""

    def __init__(self, parent, token):

        # Find our containing snippet for snippet local data
        snippet = parent
        while snippet:
            try:
                self._locals = snippet.locals
                text = snippet.visual_content.text
                mode = snippet.visual_content.mode
                context = snippet.context
                break
            except AttributeError as e:
                snippet = snippet._parent  # pylint:disable=protected-access
        self._snip = SnippetUtil(token.indent, mode, text, context, snippet)

        self._codes = ((
            'import re, os, vim, string, random',
            '\n'.join(snippet.globals.get('!p', [])).replace('\r\n', '\n'),
            token.code.replace('\\`', '`')
        ))
        NoneditableTextObject.__init__(self, parent, token)

    def _update(self, done):
        path = _vim.eval('expand("%")') or ''
        ct = self.current_text
        self._locals.update({
            't': _Tabs(self._parent),
            'fn': os.path.basename(path),
            'path': path,
            'cur': ct,
            'res': ct,
            'snip': self._snip,
        })
        self._snip._reset(ct)  # pylint:disable=protected-access

        for code in self._codes:
            try:
                exec(code, self._locals)  # pylint:disable=exec-used
            except Exception as e:
                e.snippet_code = code
                raise

        rv = as_unicode(
            self._snip.rv if self._snip._rv_changed  # pylint:disable=protected-access
            else as_unicode(self._locals['res'])
        )

        if ct != rv:
            self.overwrite(rv)
            return False
        return True
