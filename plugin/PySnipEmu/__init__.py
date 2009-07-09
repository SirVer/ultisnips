#!/usr/bin/env python
# encoding: utf-8

import glob
import os
import re
import string
import vim

from PySnipEmu.Geometry import Position
from PySnipEmu.TextObjects import *
from PySnipEmu.Buffer import VimBuffer

from PySnipEmu.debug import debug

class Snippet(object):
    _INDENT = re.compile(r"^[ \t]*")

    def __init__(self,trigger,value, descr):
        self._t = trigger
        self._v = value
        self._d = descr

    def description(self):
        return self._d
    description = property(description)

    def trigger(self):
        return self._t
    trigger = property(trigger)


    def launch(self, text_before, start):
        indent = self._INDENT.match(text_before).group(0)
        v = self._v
        if len(indent):
            lines = self._v.splitlines()
            v = lines[0]
            if len(lines) > 1:
                v += os.linesep + \
                        os.linesep.join([indent + l for l in lines[1:]])

        return SnippetInstance(StartMarker(start), v )

class VimState(object):
    def __init__(self):
        self._abs_pos = None
        self._moved = Position(0,0)

        self._lines = None
        self._dlines = None
        self._cols = None
        self._dcols = None
        self._lline = None
        self._text_changed = None

    def update(self):
        line, col = vim.current.window.cursor
        line -= 1
        abs_pos = Position(line,col)
        if self._abs_pos:
            self._moved = abs_pos - self._abs_pos
        self._abs_pos = abs_pos

        # Update buffer infos
        cols = len(vim.current.buffer[line])
        if self._cols:
            self._dcols = cols - self._cols
        self._cols = cols

        lines = len(vim.current.buffer)
        if self._lines:
            self._dlines = lines - self._lines
        self._lines = lines

        # Check if the buffer has changed in any ways
        self._text_changed = False
        # does it have more lines?
        if self._dlines:
            self._text_changed = True
        # did we stay in the same line and it has more columns now?
        elif not self.moved.line and self._dcols:
            self._text_changed = True
        # If the length didn't change but we moved a column, check if
        # the char under the cursor has changed (might be one char tab).
        elif self.moved.col == 1:
            self._text_changed = self._lline != vim.current.buffer[line]
        self._lline = vim.current.buffer[line]

    def select_range(self, r):
        delta = r.end - r.start
        lineno, col = r.start.line, r.start.col

        vim.current.window.cursor = lineno + 1, col

        if delta.col == 0:
            if (col + delta.col) == 0:
                vim.command(r'call feedkeys("\<Esc>i")')
            else:
                vim.command(r'call feedkeys("\<Esc>a")')
        else:
            # Select the word
            # Depending on the current mode and position, we
            # might need to move escape out of the mode and this
            # will move our cursor one left
            if col != 0 and vim.eval("mode()") == 'i':
                move_one_right = "l"
            else:
                move_one_right = ""

            if delta.col <= 1:
                do_select = ""
            else:
                do_select = "%il" % (delta.col-1)

            vim.command(r'call feedkeys("\<Esc>%sv%s\<c-g>")' %
                (move_one_right, do_select))


    def buf_changed(self):
        return self._text_changed
    buf_changed = property(buf_changed)

    def pos(self):
        return self._abs_pos
    pos = property(pos)

    def ppos(self):
        if not self.has_moved:
            return self.pos
        return self.pos - self.moved
    ppos = property(ppos)

    def moved(self):
        return self._moved
    moved = property(moved)

    def has_moved(self):
        return bool(self._moved.line or self._moved.col)
    has_moved = property(has_moved)

class SnippetManager(object):
    def __init__(self):
        self.reset()

        self._vstate = VimState()
        self._ctab = None

        self._expect_move_wo_change = False

    def _load_snippets_from(self, ft, fn):
        cs = None
        cv = ""
        cdescr = ""
        for line in open(fn):
            if line.startswith("#"):
                continue
            if line.startswith("snippet"):
                cs = line.split()[1]
                left = line.find('"')
                if left != -1:
                    right = line.rfind('"')
                    cdescr = line[left+1:right]
                continue
            if cs != None:
                if line.startswith("endsnippet"):
                    cv = cv[:-1] # Chop the last newline
                    l = self._snippets[ft].get(cs,[])
                    l.append(Snippet(cs,cv,cdescr))
                    self._snippets[ft][cs] = l
                    cv = ""
                    cdescr = ""
                    cs = None
                    continue
                else:
                    cv += line


    def _load_snippets_for(self, ft):
        self._snippets[ft] = {}
        for p in vim.eval("&runtimepath").split(',')[::-1]:
            pattern = p + os.path.sep + "PySnippets" + os.path.sep + \
                    "*%s.snippets" % ft

            for fn in glob.glob(pattern):
                self._load_snippets_from(ft, fn)


    def reset(self):
        self._snippets = {}
        self._csnippet = None
        self._ctab = None

    def add_snippet(self, trigger, value, descr):
        if "all" not in self._snippets:
            self._snippets["all"] = {}
        l = self._snippets["all"].get(trigger,[])
        l.append(Snippet(trigger,value, descr))
        self._snippets["all"][trigger] = l

    def _find_snippets(self, ft, trigger):
        snips = self._snippets.get(ft,None)
        if not snips:
            return []

        return snips.get(trigger, [])

    def try_expand(self, backwards = False):
        ft = vim.eval("&filetype")
        if len(ft) and ft not in self._snippets:
            self._load_snippets_for(ft)
        if "all" not in self._snippets:
            self._load_snippets_for("all")

        self._ctab = None
        self._expect_move_wo_change = False

        if self._csnippet:
            self._expect_move_wo_change = True
            self._ctab = self._csnippet.select_next_tab(backwards)
            if self._ctab is None:
                self._csnippet = None

                return True
            else:
                self._vstate.select_range(self._ctab.abs_range)

            self._vstate.update()
            return True

        lineno,col = vim.current.window.cursor
        if col == 0:
            return False

        line = vim.current.line

        if col > 0 and line[col-1] in string.whitespace:
            return False

        # Get the word to the left of the current edit position
        before,after = line[:col], line[col:]

        word = before.split()[-1]
        snippets = []
        if len(ft):
            snippets += self._find_snippets(ft, word)
        snippets += self._find_snippets("all", word)

        if not len(snippets):
            # No snippet found
            return False
        elif len(snippets) == 1:
            snippet, = snippets
        else:
            display = repr(
                [ "%i: %s" % (i+1,s.description) for i,s in
                 enumerate(snippets)
                ]
            )

            rv = vim.eval("inputlist(%s)" % display)
            if rv is None:
                return True
            rv = int(rv)
            snippet = snippets[rv-1]

        self._expect_move_wo_change = True

        text_before = before.rstrip()[:-len(word)]
        self._vb = VimBuffer(text_before, after)

        start = Position(lineno-1, len(text_before))
        self._csnippet = snippet.launch(text_before, start)

        self._vb.replace_lines(lineno-1, lineno-1, self._csnippet._current_text)

        # TODO: this code is duplicated above
        self._ctab = self._csnippet.select_next_tab()
        if self._ctab is not None:
            self._vstate.select_range(self._ctab.abs_range)

        self._vstate.update()

        return True

    def cursor_moved(self):
        self._vstate.update()

        if not self._vstate.buf_changed and not self._expect_move_wo_change:
            # Cursor moved without input.
            self._ctab = None

            # Did we leave the snippet with this movement?
            if self._csnippet and not \
               (self._vstate.pos in self._csnippet.abs_range):
                self.reset()

        if not self._ctab:
            return

        if self._vstate.buf_changed and self._ctab:
            if 0 <= self._vstate.moved.line <= 1:
                # Detect a carriage return
                if self._vstate.moved.col <= 0 and self._vstate.moved.line == 1:
                    self._chars_entered('\n')
                elif self._vstate.moved.col < 0: # Some deleting was going on
                    sline = self._csnippet.abs_start.line
                    dlines = self._csnippet.end.line - self._csnippet.start.line

                    self._csnippet.backspace(-self._vstate.moved.col)
                    # Replace
                    self._vb.replace_lines(sline, sline + dlines,
                                           self._csnippet._current_text)

                    ct_end = self._ctab.abs_end
                    vim.current.window.cursor = ct_end.line +1, ct_end.col

                    self._vstate.update()
                else:
                    line = vim.current.line

                    chars = line[self._vstate.pos.col - self._vstate.moved.col:
                                 self._vstate.pos.col]
                    self._chars_entered(chars)


        self._expect_move_wo_change = False

    def entered_insert_mode(self):
        self._vstate.update()
        if self._csnippet and self._vstate.has_moved:
            self.reset()

    def _chars_entered(self, chars):
        sline = self._csnippet.abs_start.line
        dlines = self._csnippet.end.line - self._csnippet.start.line

        if self._csnippet._tab_selected:
            self._ctab.current_text = chars
            self._csnippet._tab_selected = False
        else:
            self._ctab.current_text += chars
        
        self._csnippet.update()
            
        # Replace
        dlines += self._vstate.moved.line
        self._vb.replace_lines(sline, sline + dlines,
                       self._csnippet._current_text)
        ct_end = self._ctab.abs_end
        vim.current.window.cursor = ct_end.line +1, ct_end.col

        self._vstate.update()

    def backspace(self):
        # BS was called in select mode

        if self._csnippet and self._csnippet.tab_selected:
            # This only happens when a default value is delted using backspace
            old_range = self._csnippet.abs_range
            vim.command(r'call feedkeys("i")')
            self._chars_entered('')


        else:
            vim.command(r'call feedkeys("\<BS>")')

PySnipSnippets = SnippetManager()

