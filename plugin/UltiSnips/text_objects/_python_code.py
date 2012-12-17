#!/usr/bin/env python
# encoding: utf-8

import os
from collections import namedtuple

import UltiSnips._vim as _vim
from UltiSnips.compatibility import compatible_exec, as_unicode
from UltiSnips.util import IndentUtil

from UltiSnips.text_objects._base import NoneditableTextObject


class _Tabs(object):
    def __init__(self, to):
        self._to = to

    def __getitem__(self, no):
        ts = self._to._get_tabstop(self._to, int(no))
        if ts is None:
            return ""
        return ts.current_text

_VisualContent = namedtuple('_VisualContent', ['mode', 'text'])


class SnippetUtil(object):
    """ Provides easy access to indentation, etc.
    """

    def __init__(self, initial_indent, vmode, vtext):
        self._ind = IndentUtil()
        self._visual = _VisualContent(vmode, vtext)

        self._initial_indent = self._ind.indent_to_spaces(initial_indent)

        self._reset("")

    def _reset(self, cur):
        """ Gets the snippet ready for another update.

        :cur: the new value for c.
        """
        self._ind.reset()
        self._c = cur
        self._rv = ""
        self._changed = False
        self.reset_indent()

    def shift(self, amount=1):
        """ Shifts the indentation level.
        Note that this uses the shiftwidth because thats what code
        formatters use.

        :amount: the amount by which to shift.
        """
        self.indent += " " * self._ind.sw * amount

    def unshift(self, amount=1):
        """ Unshift the indentation level.
        Note that this uses the shiftwidth because thats what code
        formatters use.

        :amount: the amount by which to unshift.
        """
        by = -self._ind.sw * amount
        try:
            self.indent = self.indent[:by]
        except IndexError:
            self.indent = ""

    def mkline(self, line="", indent=None):
        """ Creates a properly set up line.

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
                    indent = ""
            indent = self._ind.spaces_to_indent(indent)

        return indent + line

    def reset_indent(self):
        """ Clears the indentation. """
        self.indent = self._initial_indent

    # Utility methods
    @property
    def fn(self):
        """ The filename. """
        return _vim.eval('expand("%:t")') or ""

    @property
    def basename(self):
        """ The filename without extension. """
        return _vim.eval('expand("%:t:r")') or ""

    @property
    def ft(self):
        """ The filetype. """
        return self.opt("&filetype", "")

    # Necessary stuff
    def rv():
        """ The return value.
        This is a list of lines to insert at the
        location of the placeholder.

        Deprecates res.
        """
        def fget(self):
            return self._rv

        def fset(self, value):
            self._changed = True
            self._rv = value
        return locals()
    rv = property(**rv())

    @property
    def _rv_changed(self):
        """ True if rv has changed. """
        return self._changed

    @property
    def c(self):
        """ The current text of the placeholder.

        Deprecates cur.
        """
        return self._c

    @property
    def v(self):
        """Content of visual expansions"""
        return self._visual

    def opt(self, option, default=None):
        """ Gets a Vim variable. """
        if _vim.eval("exists('%s')" % option) == "1":
            try:
                return _vim.eval(option)
            except _vim.error:
                pass
        return default

    # Syntatic sugar
    def __add__(self, value):
        """ Appends the given line to rv using mkline. """
        self.rv += '\n'  # handles the first line properly
        self.rv += self.mkline(value)
        return self

    def __lshift__(self, other):
        """ Same as unshift. """
        self.unshift(other)

    def __rshift__(self, other):
        """ Same as shift. """
        self.shift(other)


class PythonCode(NoneditableTextObject):
    def __init__(self, parent, token):
        code = token.code.replace("\\`", "`")

        # Find our containing snippet for snippet local data
        snippet = parent
        while snippet:
            try:
                self._locals = snippet.locals
                t = snippet.visual_content.text
                m = snippet.visual_content.mode
                break
            except AttributeError:
                snippet = snippet._parent
        self._snip = SnippetUtil(token.indent, m, t)

        self._globals = {}
        globals = snippet.globals.get("!p", [])
        compatible_exec("\n".join(globals).replace("\r\n", "\n"), self._globals)

        # Add Some convenience to the code
        self._code = "import re, os, vim, string, random\n" + code

        NoneditableTextObject.__init__(self, parent, token)

    def _update(self, done, not_done):
        path = _vim.eval('expand("%")')
        if path is None:
            path = ""
        fn = os.path.basename(path)

        ct = self.current_text
        self._snip._reset(ct)
        local_d = self._locals

        local_d.update({
            't': _Tabs(self._parent),
            'fn': fn,
            'path': path,
            'cur': ct,
            'res': ct,
            'snip': self._snip,
        })

        compatible_exec(self._code, self._globals, local_d)

        rv = as_unicode(
            self._snip.rv if self._snip._rv_changed
            else as_unicode(local_d['res'])
        )

        if ct != rv:
            self.overwrite(rv)
            return False
        return True
