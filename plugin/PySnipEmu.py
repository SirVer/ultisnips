#!/usr/bin/env python
# encoding: utf-8

import glob
import os
import re
import string
import vim

from TextObjects import *
from Geometry import Position

from debug import debug

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


    def launch(self, before, after):
        lineno, col = vim.current.window.cursor
        start = Position(lineno-1,col - len(self._t))
        end = Position(lineno-1,col)

        line = vim.current.line

        text_before = line[:start.col]
        text_after = line[end.col:]

        indent = self._INDENT.match(text_before).group(0)
        v = self._v
        if len(indent):
            lines = self._v.splitlines()
            v = lines[0]
            if len(lines) > 1:
                v += os.linesep + \
                        os.linesep.join([indent + l for l in lines[1:]])

        s = SnippetInstance(start, end, v, text_before, text_after)

        if s.has_tabs():
            s.select_next_tab()
            return s
        else:
            vim.current.window.cursor = s.end.line + 1, s.end.col

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
            debug("self._ll: %s" % (self._lline))
            debug("vim.current.buffer[line]: %s" % (vim.current.buffer[line]))

            self._text_changed = self._lline != vim.current.buffer[line]
        self._lline = vim.current.buffer[line]

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
        self._accept_input = False

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
        self._current_snippets = []

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

        self._accept_input = False
        self._expect_move_wo_change = False

        if len(self._current_snippets):
            cs = self._current_snippets[-1]
            self._expect_move_wo_change = True
            if not cs.select_next_tab(backwards):

                # HACK: only jump to end if there is no zero defined. This
                # TODO: this jump should be inside select_next_tab or even
                # better: when the snippet is launched and no parent snippet is
                # defined, a $0 should be appended to the end of it and this
                # extra code should be ignored Jump to the end of the snippet
                # and enter insert mode
                cs = self._current_snippets[-1]
                if 0 not in cs._tabstops:
                    vim.current.window.cursor = cs.end.line +1, cs.end.col
                    vim.command(r'call feedkeys("\<Esc>a")')
                self._current_snippets.pop()

                return True

            self._vstate.update()
            self._accept_input = True
            return True

        dummy,col = vim.current.window.cursor
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
        s = snippet.launch(before.rstrip()[:-len(word)], after)

        self._vstate.update()
        if s is not None:
            self._current_snippets.append(s)
            self._accept_input = True


        return True

    def cursor_moved(self):
        debug("Cursor moved")

        self._vstate.update()

        debug("self._vstate._dlines: %s" % (self._vstate._dlines))
        debug("self._vstate._dcols: %s" % (self._vstate._dcols))
        debug("self._vstate.buf_changed: %s" % (self._vstate.buf_changed))
        if not self._vstate.buf_changed and not self._expect_move_wo_change:
            # Cursor moved without input.
            self._accept_input = False

            # Did we leave the snippet with this movement?
            debug("Checking if we left the snippet")
            debug("self._vstate.pos: %s" % (self._vstate.pos))

            if len(self._current_snippets):
                cs = self._current_snippets[-1]
                debug("cs.span: %s" % (cs.span))

                is_inside = self._vstate.pos in cs.span

                debug("is_inside: %s" % (is_inside))

                if not is_inside:
                    self._current_snippets.pop()

        if not self._accept_input:
            return

        if self._vstate.buf_changed and len(self._current_snippets):
            if 0 <= self._vstate.moved.line <= 1:
                cs = self._current_snippets[-1]

                # Detect a carriage return
                if self._vstate.moved.col < 0 and self._vstate.moved.line == 1:
                    # Hack, remove a line in vim, because we are going to
                    # overwrite the old line range with the new snippet value.
                    # After the expansion, we put the cursor were the user left
                    # it. This action should be completely transparent for the
                    # user
                    cache_pos = vim.current.window.cursor
                    del vim.current.buffer[self._vstate.pos.line-1]
                    cs.chars_entered('\n', self._vstate)
                    vim.current.window.cursor = cache_pos
                elif self._vstate.moved.col < 0: # Some deleting was going on
                    cs.backspace(-self._vstate.moved.col, self._vstate)
                else:
                    line = vim.current.line

                    chars = line[self._vstate.pos.col - self._vstate.moved.col:
                                 self._vstate.pos.col]
                    cs.chars_entered(chars, self._vstate)

            self._vstate.update()

        self._expect_move_wo_change = False

    def entered_insert_mode(self):
        debug("Entered insert mode")

        self._vstate.update()
        debug("self._vstate.has_moved: %s" % (self._vstate.has_moved))
        if len(self._current_snippets) and \
           self._vstate.has_moved:
           # not self._current_snippets[-1].tab_selected and \

            self._current_snippets = []

    def backspace(self):
        # BS was called in select mode

        if len(self._current_snippets) and \
           self._current_snippets[-1].tab_selected:
            # This only happens when a default value is delted using backspace
            vim.command(r'call feedkeys("i")')
            cs = self._current_snippets[-1]
            cs.chars_entered('', self._vstate)
            self._vstate.update()
        else:
            vim.command(r'call feedkeys("\<BS>")')

PySnipSnippets = SnippetManager()

