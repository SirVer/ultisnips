#!/usr/bin/env python
# encoding: utf-8

import vim
import string
import re

class TabStop(object):
    def __init__(self, no, idx, span, default_text = ""):
        self._no = no
        self._default_text = default_text
        self._span = span
        self._lineidx = idx

    def line_idx(self):
        return self._lineidx
    line_idx = property(line_idx)

    def span(self):
        return self._span
    span = property(span)

    def default_text(self):
        return self._default_text
    default_text = property(default_text)

    def number(self):
        return self._no
    number = property(number)

class Snippet(object):
    _TB_EXPR = re.compile(r'\$(?:(?:{(\d+):(.*)})|(\d+))')

    def __init__(self,trigger,value):
        self._t = trigger
        self._v = value

    def trigger(self):
        return self._t
    trigger = property(trigger)

    def _find_text_tabstops(self, lines):
        tabstops = []

        for idx in range(len(lines)):
            line = lines[idx]
            m = self._TB_EXPR.search(line)
            while m is not None:
                if m.group(1):
                    no = int(m.group(1))
                    def_text = m.group(2)
                else:
                    no = int(m.group(3))
                    def_text = ""


                start, end = m.span()
                line = line[:start] + def_text + line[end:]

                ts = TabStop(no, idx, (start,start+len(def_text)), def_text)

                lines[idx] = line

                tabstops.append( (ts.number, ts) )

                m = self._TB_EXPR.search(line)

        tabstops.sort()

        return tabstops

    def _replace_tabstops(self):
        lines = self._v.split('\n')

        ts = self._find_text_tabstops(lines)

        return ts, lines

    def put(self, before, after):
        lineno,col = vim.current.window.cursor

        col -= len(self._t)

        ts,lines = self._replace_tabstops()

        endcol = None
        if len(ts):
            zts = ts[0][1]
            newline = lineno + zts.line_idx
            if newline == lineno:
                newcol = col + zts.span[0]
                endcol = col + zts.span[1]
            else:
                newcol = zts.span[0]
                endcol = zts.span[1]
        else:
            newline = lineno + len(lines) - 1
            if len(lines) == 1:
                newcol = col + len(lines[-1])
            else:
                newcol = len(lines[-1])


        lines[0] = before + lines[0]
        lines[-1] += after

        vim.current.buffer[lineno-1:lineno-1+len(lines)] = lines

        vim.current.window.cursor = newline, newcol

        # if endcol:
        #     # Select the word
        #     vim.command("insert PyVimSnips_SelectWord(%i)"  % (endcol-newcol))


class SnippetManager(object):
    def __init__(self):
        self.clear_snippets()

    def add_snippet(self,trigger,value):
        self._snippets[trigger] = Snippet(trigger,value)

    def clear_snippets(self):
        self._snippets = {}

    def try_expand(self):
        line = vim.current.line

        dummy,col = vim.current.window.cursor

        if col > 0 and line[col-1] in string.whitespace:
            return

        # Get the word to the left of the current edit position
        before,after = line[:col], line[col:]

        word = before.split()[-1]
        if word in self._snippets:
            self._snippets[word].put(before.rstrip()[:-len(word)], after)


PySnipSnippets = SnippetManager()
