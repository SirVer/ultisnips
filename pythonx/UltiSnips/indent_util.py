#!/usr/bin/env python3
# encoding: utf-8

"""See module doc."""

from UltiSnips import vim_helper


class IndentUtil:

    """Utility class for dealing properly with indentation."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Gets the spacing properties from Vim."""
        self.shiftwidth = int(
            vim_helper.eval("exists('*shiftwidth') ? shiftwidth() : &shiftwidth")
        )
        self._expandtab = vim_helper.eval("&expandtab") == "1"
        self._tabstop = int(vim_helper.eval("&tabstop"))

    def ntabs_to_proper_indent(self, ntabs):
        """Convert 'ntabs' number of tabs to the proper indent prefix."""
        line_ind = ntabs * self.shiftwidth * " "
        line_ind = self.indent_to_spaces(line_ind)
        line_ind = self.spaces_to_indent(line_ind)
        return line_ind

    def indent_to_spaces(self, indent):
        """Converts indentation to spaces respecting Vim settings."""
        indent = indent.expandtabs(self._tabstop)
        right = (len(indent) - len(indent.rstrip(" "))) * " "
        indent = indent.replace(" ", "")
        indent = indent.replace("\t", " " * self._tabstop)
        return indent + right

    def spaces_to_indent(self, indent):
        """Converts spaces to proper indentation respecting Vim settings."""
        if not self._expandtab:
            indent = indent.replace(" " * self._tabstop, "\t")
        return indent
