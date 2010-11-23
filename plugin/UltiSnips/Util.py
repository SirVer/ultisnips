#!/usr/bin/env python
# encoding: utf-8

import vim
import os

class IndentUtil(object):
    """ Utility class for dealing properly with indentation. """

    def __init__(self):
        self.reset()

    def reset(self):
        """ Gets the spacing properties from vim. """
        self.sw = int(vim.eval("&sw"))
        self.sts = int(vim.eval("&sts"))
        self.et = (vim.eval("&expandtab") == "1")
        self.ts = int(vim.eval("&ts"))

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

    def indent_to_spaces(self, indent):
        """ Converts indentation to spaces respecting vim settings. """
        indent = self._strip_tabs(indent, self.ts)
        right = (len(indent) - len(indent.rstrip(" "))) * " "
        indent = indent.replace(" ", "")
        indent = indent.replace('\t', " " * self.ts)
        return indent + right

    def spaces_to_indent(self, indent):
        """ Converts spaces to proper indentation respecting vim settings """
        if not self.et:
            indent = indent.replace(" " * self.ts, '\t')
        return indent
