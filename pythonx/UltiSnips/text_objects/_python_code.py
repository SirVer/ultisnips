#!/usr/bin/env python
# encoding: utf-8

"""Implements `!p ` interpolation."""

import os
from collections import namedtuple

from UltiSnips import _vim
from UltiSnips.compatibility import as_unicode
from UltiSnips.indent_util import IndentUtil
from UltiSnips.text_objects._base import NoneditableTextObject


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

_VisualContent = namedtuple('_VisualContent', ['mode', 'text'])


class SnippetUtil(object):

    """Provides easy access to indentation, etc.

    This is the 'snip' object in python code.

    """

    def __init__(self, initial_indent, vmode, vtext):
        self._ind = IndentUtil()
        self._visual = _VisualContent(vmode, vtext)
        self._initial_indent = self._ind.indent_to_spaces(initial_indent)
        self._reset('')

    def _reset(self, cur):
        """Gets the snippet ready for another update.

        :cur: the new value for c.

        """
        self._ind.reset()
        self._cur = cur
        self._rv = ''
        self._changed = False
        self._package = None
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
    def dirname(self):  # pylint: disable=no-self-use
        """The filename's directory."""
        return _vim.eval('expand("%:p:h")') or ''

    @property
    def package(self):
        """
        Try our best to detect the python package name where this
        snip is being used.
        """
        if self._package is None:
            package = []
            curdir = self.dirname
            while True:
                if os.path.isfile(os.path.join(curdir, '__init__.py')):
                    package.append(os.path.basename(curdir))
                    curdir = os.path.abspath(os.path.join(curdir, '..'))
                    continue
                break

            if package:
                package.reverse()
                self._package = '.'.join(package)
        return self._package

    @property
    def module(self):
        """
        Try our best to detect the python module name where this snippet
        is being used.
        """
        if not self.package:
            return ''
        if self.basename == '__init__':
            return self.package
        return '{0}.{1}'.format(self.package, self.basename)

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
                break
            except AttributeError:
                snippet = snippet._parent  # pylint:disable=protected-access
        self._snip = SnippetUtil(token.indent, mode, text)

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
            exec(code, self._locals)  # pylint:disable=exec-used

        rv = as_unicode(
            self._snip.rv if self._snip._rv_changed  # pylint:disable=protected-access
            else as_unicode(self._locals['res'])
        )

        if ct != rv:
            self.overwrite(rv)
            return False
        return True
