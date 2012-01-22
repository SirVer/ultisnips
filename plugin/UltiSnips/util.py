#!/usr/bin/env python
# encoding: utf-8

import os
import types

import UltiSnips._vim as _vim

class IndentUtil(object):
    """ Utility class for dealing properly with indentation. """

    def __init__(self):
        self.reset()

    def reset(self):
        """ Gets the spacing properties from Vim. """
        self.sw = int(_vim.eval("&sw"))
        self.sts = int(_vim.eval("&sts"))
        self.et = (_vim.eval("&expandtab") == "1")
        self.ts = int(_vim.eval("&ts"))

        # The amount added when pressing tab in insert mode
        self.ind_len = self.sts or self.ts

    def _strip_tabs(self, indent, ts):
        new_ind = []
        for ch in indent:
            if ch == '\t':
                new_ind.append(" " * (ts - (len(new_ind) % ts)))
            else:
                new_ind.append(ch)
        return "".join(new_ind)

    def ntabs_to_proper_indent(self, ntabs):
        line_ind = ntabs * self.sw * " "
        line_ind = self.indent_to_spaces(line_ind)
        line_ind = self.spaces_to_indent(line_ind)
        return line_ind

    def indent_to_spaces(self, indent):
        """ Converts indentation to spaces respecting Vim settings. """
        indent = self._strip_tabs(indent, self.ts)
        right = (len(indent) - len(indent.rstrip(" "))) * " "
        indent = indent.replace(" ", "")
        indent = indent.replace('\t', " " * self.ts)
        return indent + right

    def spaces_to_indent(self, indent):
        """ Converts spaces to proper indentation respecting Vim settings """
        if not self.et:
            indent = indent.replace(" " * self.ts, '\t')
        return indent
