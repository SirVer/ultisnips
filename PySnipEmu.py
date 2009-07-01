#!/usr/bin/env python
# encoding: utf-8

import vim
import string
import re

class Mirror(object):
    def __init__(self, ts, idx, start):
        self._ts = ts
        self._start = (idx, start)
        self._end = (idx,start)
        self._delta_rows = 0
        self._delta_cols = 0

    def delta_rows():
        doc = "The RW foo property."
        def fget(self):
            return self._delta_rows
        def fset(self, value):
            self._delta_rows = value
        return locals()
    delta_rows = property(**delta_rows())

    def delta_cols():
        doc = "The RW foo property."
        def fget(self):
            return self._delta_cols
        def fset(self, value):
            self._delta_cols = value
        return locals()
    delta_cols = property(**delta_cols())

    @property
    def tabstop(self):
        return self._ts

    @property
    def number(self):
        return self._no

    @property
    def start(self):
        "The RO foo property."
        return self._start

    @property
    def end(self):
        "The RO foo property."
        return self._end


    def update_span(self):
        start = self._start
        lines = self._ts.current_text.splitlines()
        if len(lines) == 1:
            self._end = (start[0]+len(lines)-1,len(lines[-1]))
        elif len(lines) > 1:
            self._end = (start[0],start[1]+len(lines[0]) )

class TabStop(object):
    def __init__(self, no, idx, span, default_text = ""):
        self._no = no
        self._default_text = default_text
        self._start = span[0]
        self._lineidx = idx
        self._ct = default_text

    def current_text():
        def fget(self):
            return self._ct
        def fset(self, value):
            self._ct = value
        return locals()
    current_text = property(**current_text())

    def line_idx(self):
        return self._lineidx
    line_idx = property(line_idx)

    def span(self):
        return (self._start,self._start+len(self._ct))
    span = property(span)

    def default_text(self):
        return self._default_text
    default_text = property(default_text)

    def number(self):
        return self._no
    number = property(number)

class SnippetInstance(object):
    def __init__(self,start,end, ts, mirrors):
        self._start = start
        self._end = end
        self._ts = ts
        self._mirrors = mirrors

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
        if endcol-newcol > 0:
            if newcol != 0 and vim.eval("mode()") == 'i':
                move_one_right = "l"
            else:
                move_one_right = ""

            vim.command(r'call feedkeys("\<Esc>%sv%il\<c-g>")'
                % (move_one_right, endcol-newcol-1))

    def _update_mirrors(self,for_ts):
        for m in self._mirrors:
            if m.tabstop == for_ts:
                mirror_line = m.start[0]
                line = vim.current.buffer[mirror_line]
                line = line[:m.start[1]+m.delta_cols] + for_ts.current_text # + line[m.end[1]+m.delta_cols:]
                vim.current.buffer[mirror_line] = line

                # m.update_span()

                # Now update all mirrors and tabstops, that they have moved
                # lines = for_ts.current_text.splitlines()
                # if len(lines):
                #     for om in self._mirrors:
                #         om.update_span()
                #
                #         # if om.start[0] > m.start[0]:
                #         #     om.delta_rows += len(lines)-1
                #         if om.start[0] == m.start[0]:
                #             if om.start[1] >= m.start[1]:
                #                 om.delta_cols += len(lines[-1])

    def _move_to_on_line(self,amount):
        lineno,col = vim.current.window.cursor
        lineno -= 1
        for m in self._mirrors:
            if m.start[0] != lineno:
                continue
            if m.start[1] > col:
                m.delta_cols += amount


    def backspace(self,count):
        if self._cts not in self._ts:
            if 0 in self._ts:
                self._cts = 0
            else:
                self._cts = 1

        cts = self._ts[self._cts]
        cts.current_text = cts.current_text[:-count]

        # self._move_to_on_line(-count)

        self._update_mirrors(cts)

    def chars_entered(self, chars):
        if self._cts not in self._ts:
            if 0 in self._ts:
                self._cts = 0
            else:
                self._cts = 1

        cts = self._ts[self._cts]
        cts.current_text += chars

        self._move_to_on_line(len(chars))

        self._update_mirrors(cts)


class Snippet(object):
    _TABSTOP = re.compile(r'''(?xms)
(?:\${(\d+):(.*?)})|   # A simple tabstop with default value
(?:\$(\d+))           # A mirror or a tabstop without default value.
''')

    def __init__(self,trigger,value):
        self._t = trigger
        self._v = value

    def trigger(self):
        return self._t
    trigger = property(trigger)

    def _handle_tabstop(self, m, val, tabstops, mirrors):
        no = int(m.group(1))
        def_text = m.group(2)

        start, end = m.span()
        val = val[:start] + def_text + val[end:]

        line_idx = val[:start].count('\n')
        line_start = val[:start].rfind('\n') + 1
        start_in_line = start - line_start
        ts = TabStop(no, line_idx, (start_in_line,start_in_line+len(def_text)), def_text)

        tabstops[ts.number] = ts

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
            ts = TabStop(no, line_idx, (start_in_line,start_in_line), "")
            tabstops[ts.number] = ts

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

        return tabstops, mirrors, val

    def _replace_tabstops(self):
        ts, mirrors, val = self._find_tabstops(self._v)
        lines = val.split('\n')

        return ts, mirrors, lines

    def launch(self, before, after):
        lineno,col = vim.current.window.cursor

        col -= len(self._t)

        ts, mirrors, lines = self._replace_tabstops()

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
        cp = vim.current.window.cursor

        if and len(self._current_snippets) and self._last_cursor_pos is not None:
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
