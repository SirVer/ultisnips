#!/usr/bin/env python
# encoding: utf-8

import vim
import string
import re

def debug(s):
    f = open("/tmp/file.txt","a")
    f.write(s+'\n')
    f.close()

class TextObject(object):
    """
    This base class represents any object in the text
    that has a span in any ways
    """
    def __init__(self, start, end):
        self._start = start
        self._end = end

        self._delta_rows = 0
        self._delta_cols = 0

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def delta_rows():
        def fget(self):
            return self._delta_rows
        def fset(self, value):
            self._delta_rows = value
        return locals()
    delta_rows = property(**delta_rows())

    def delta_cols():
        def fget(self):
            return self._delta_cols
        def fset(self, value):
            self._delta_cols = value
        return locals()
    delta_cols = property(**delta_cols())


class Mirror(TextObject):
    """
    A Mirror object mirrors a TabStop that is, text is repeated here
    """
    def __init__(self, ts, idx, start):
        TextObject.__init__(self, (idx,start), (idx,start))

        self._tabstop = ts

    @property
    def tabstop(self):
        return self._tabstop

    def update(self,ts):
        if ts != self._tabstop:
            return 0

        mirror_line = self.start[0]
        line = vim.current.buffer[mirror_line]

        line = line[:self.start[1]+self.delta_cols] + \
                self._tabstop.current_text + \
                line[self.end[1]+self.delta_cols:]

        oldspan = self.end[1]-self.start[1]
        self._end = (self.start[0],self.start[1]+len(self._tabstop.current_text))
        newspan = self.end[1]-self.start[1]

        vim.current.buffer[mirror_line] = line

        return newspan-oldspan


class TabStop(TextObject):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, idx, span, default_text = ""):
        TextObject.__init__(self, (idx,span[0]), (idx,span[1]))

        self._ct = default_text

    def current_text():
        def fget(self):
            return self._ct
        def fset(self, value):
            self._ct = value
        return locals()
    current_text = property(**current_text())

    @property
    def span(self):
        return (self._start[1]+self._delta_cols,self._start[1]+self._delta_cols+len(self._ct))

class SnippetInstance(TextObject):
    """
    A Snippet instance is an instance of a Snippet Definition. That is,
    when the user expands a snippet, a SnippetInstance is created to
    keep track of the corresponding TextObjects. The Snippet itself is
    also a TextObject because it has a start an end
    """

    def __init__(self,start,end, ts, mirrors):
        TextObject.__init__(self, start, end)

        self._tabstops = ts
        self._mirrors = mirrors
        self._text_objects = ts.values() + mirrors
        self._selected_tab = None

        self._cts = None

        for ts in self._tabstops.values():
            self._update_mirrors(ts)

    def select_next_tab(self, backwards = False):
        if self._cts == 0:
            if not backwards:
                return False

        if backwards:
            cts_bf = self._cts

            if self._cts == 0:
                self._cts = max(self._tabstops.keys())
            else:
                self._cts -= 1
            if self._cts <= 0:
                self._cts = cts_bf
        else:
            # All tabs handled?
            if self._cts is None:
                self._cts = 1
            else:
                self._cts += 1

            if self._cts not in self._tabstops:
                self._cts = 0
                if 0 not in self._tabstops:
                    return False

        ts = self._tabstops[self._cts]
        lineno, col = self._start

        newline = lineno + ts.start[0]
        if newline == lineno:
            newcol = col + ts.span[0]
            endcol = col + ts.span[1]
        else:
            newcol = ts.span[0]
            endcol = ts.span[1]

        vim.current.window.cursor = newline, newcol

        # Select the word
        # Depending on the current mode and position, we
        # might need to move escape out of the mode and this
        # will move our cursor one left
        if endcol-newcol > 0:
            if newcol != 0 and vim.eval("mode()") == 'i':
                move_one_right = "l"
            else:
                move_one_right = ""

            vim.command(r'call feedkeys("\<Esc>%sv%il\<c-g>")'
                % (move_one_right, endcol-newcol-1))
            self._selected_tab = ts

        return True


    def _update_mirrors(self,for_ts):
        for m in self._mirrors:
            moved = m.update(for_ts)
            if moved:
                self._move_to_on_line(moved, m.start[0], m.start[1]+m.delta_cols,cobj=m)


    def _move_to_on_line(self,amount, lineno = None, col = None, cobj = None):
        if self._cts is None:
            return

        if lineno is None and col is None:
            lineno,col = vim.current.window.cursor
            lineno -= 1
            cobj = self._tabstops[self._cts]

        for m in self._text_objects:
            if m.start[0] != lineno:
                continue
            if m.start[1]+m.delta_cols >= col and m != cobj:
                m.delta_cols += amount


    def backspace(self,count):
        cts = self._tabstops[self._cts]
        ll = len(cts.current_text)

        cts.current_text = cts.current_text[:-count]
        self._move_to_on_line(len(cts.current_text)-ll)

        self._update_mirrors(cts)

    def chars_entered(self, chars):
        cts = self._tabstops[self._cts]

        if self._selected_tab is not None:
            self._move_to_on_line(len(chars)-len(cts.current_text))
            cts.current_text = ""
            self._selected_tab = None
        else:
            self._move_to_on_line(len(chars))

        cts.current_text += chars

        self._update_mirrors(cts)


class Snippet(object):
    _TABSTOP = re.compile(r'''(?xms)
(?:\${(\d+):(.*?)})|   # A simple tabstop with default value
(?:\$(\d+))           # A mirror or a tabstop without default value.
''')

    def __init__(self,trigger,value):
        self._t = trigger
        self._v = value

    @property
    def trigger(self):
        return self._t

    def _handle_tabstop(self, m, val, tabstops, mirrors):
        no = int(m.group(1))
        def_text = m.group(2)

        start, end = m.span()
        val = val[:start] + def_text + val[end:]

        line_idx = val[:start].count('\n')
        line_start = val[:start].rfind('\n') + 1
        start_in_line = start - line_start
        ts = TabStop(line_idx, (start_in_line,start_in_line+len(def_text)), def_text)

        tabstops[no] = ts

        return val

    def _handle_ts_or_mirror(self, m, val, tabstops, mirrors):
        no = int(m.group(3))

        start, end = m.span()
        val = val[:start] + val[end:]

        line_idx = val[:start].count('\n')
        line_start = val[:start].rfind('\n') + 1
        start_in_line = start - line_start

        if no in tabstops:
            m = Mirror(tabstops[no], line_idx, start_in_line)
            mirrors.append(m)
        else:
            ts = TabStop(line_idx, (start_in_line,start_in_line))
            tabstops[no] = ts

        return val

    def _find_tabstops(self, val):
        tabstops = {}
        mirrors = []

        while 1:
            m = self._TABSTOP.search(val)

            if m is not None:
                if m.group(1) is not None: # ${1:hallo}
                    val = self._handle_tabstop(m,val,tabstops,mirrors)
                elif m.group(3) is not None: # $1
                    val = self._handle_ts_or_mirror(m,val,tabstops,mirrors)
            else:
                break

        return tabstops, mirrors, val.split('\n')

    def launch(self, before, after):
        lineno,col = vim.current.window.cursor

        col -= len(self._t)

        ts, mirrors, lines = self._find_tabstops(self._v)

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

        if len(ts) or len(mirrors):
            s = SnippetInstance( (lineno,col), (newline,newcol), ts, mirrors)

            s.select_next_tab()

            return s

class SnippetManager(object):
    def __init__(self):
        self.reset()
        self._last_cursor_pos = None

    def reset(self):
        self._snippets = {}
        self._current_snippets = []

    def add_snippet(self,trigger,value):
        self._snippets[trigger] = Snippet(trigger,value)

    def try_expand(self, backwards = False):
        if len(self._current_snippets):
            cs = self._current_snippets[-1]
            if not cs.select_next_tab(backwards):
                self._current_snippets.pop()
            self._last_cursor_pos = vim.current.window.cursor
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
            self._last_cursor_pos = vim.current.window.cursor
            if s is not None:
                self._current_snippets.append(s)

    def cursor_moved(self):
        cp = vim.current.window.cursor

        if len(self._current_snippets) and self._last_cursor_pos is not None:
            lineno,col = cp
            llineo,lcol = self._last_cursor_pos
            # If we moved the line, somethings fishy.
            if lineno == self._last_cursor_pos[0]:
                cs = self._current_snippets[-1]

                if lcol > col: # Some deleting was going on
                    cs.backspace(lcol-col)
                else:
                    line = vim.current.line

                    chars = line[lcol:col]
                    cs.chars_entered(chars)

        self._last_cursor_pos = cp

    def entered_insert_mode(self):
        pass

PySnipSnippets = SnippetManager()

