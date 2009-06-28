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

class SnippetInstance(object):
    def __init__(self,start,end, ts):
        self._start = start
        self._end = end
        self._ts = ts
        
        self._cts = 1

    def select_next_tab(self):
        if self._cts not in self._ts:
            if 0 in self._ts:
                self._cts = 0
            else:
                self._cts = 1
        
        ts = self._ts[self._cts]
        lineno, col = self._start

        newline = lineno + ts.line_idx
        if newline == lineno:
            newcol = col + ts.span[0]
            endcol = col + ts.span[1]
        else:
            newcol = ts.span[0]
            endcol = ts.span[1]
        
        self._cts += 1

        vim.current.window.cursor = newline, newcol
        
        # Select the word
       
        # Depending on the current mode and position, we
        # might need to move escape out of the mode and this
        # will move our cursor one left
        if newcol != 0 and vim.eval("mode()") == 'i':
            move_one_right = "l"
        else:
            move_one_right = ""

        vim.command(r'call feedkeys("\<Esc>%sv%il\<c-g>")'
            % (move_one_right, endcol-newcol-1))

class Snippet(object):
    _TB_EXPR = re.compile(r'\$(?:(?:{(\d+):(.*?)})|(\d+))')

    def __init__(self,trigger,value):
        self._t = trigger
        self._v = value

    def trigger(self):
        return self._t
    trigger = property(trigger)

    def _find_text_tabstops(self, lines):
        tabstops = {}

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

                tabstops[ts.number] = ts

                m = self._TB_EXPR.search(line)

        return tabstops

    def _replace_tabstops(self):
        lines = self._v.split('\n')

        ts = self._find_text_tabstops(lines)

        return ts, lines

    def launch(self, before, after):
        lineno,col = vim.current.window.cursor

        col -= len(self._t)

        ts,lines = self._replace_tabstops()

        endcol = None
        newline = 1
        newcol = 0
        if not len(ts):
            newline = lineno + len(lines) - 1
            if len(lines) == 1:
                newcol = col + len(lines[-1])
            else:
                newcol = len(lines[-1])
        
        lines[0] = before + lines[0]
        lines[-1] += after

        vim.current.buffer[lineno-1:lineno-1+len(lines)] = lines

        vim.current.window.cursor = newline, newcol
        
        if len(ts):
            s = SnippetInstance( (lineno,col), (newline,newcol), ts)
            
            s.select_next_tab()
            
            return s


class SnippetManager(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.clear_snippets()
        self._current_snippets = []

    def add_snippet(self,trigger,value):
        self._snippets[trigger] = Snippet(trigger,value)

    def clear_snippets(self):
        self._snippets = {}

    def try_expand(self):
        if len(self._current_snippets):
            self._current_snippets[-1].select_next_tab()
            return

        line = vim.current.line

        dummy,col = vim.current.window.cursor

        if col > 0 and line[col-1] in string.whitespace:
            return

        # Get the word to the left of the current edit position
        before,after = line[:col], line[col:]

        word = before.split()[-1]
        if word in self._snippets:
            s = self._snippets[word].launch(before.rstrip()[:-len(word)], after)
            if s is not None:
                self._current_snippets.append(s)
    
    def cursor_moved(self):
        pass

    def entered_insert_mode(self):
        pass

PySnipSnippets = SnippetManager()
