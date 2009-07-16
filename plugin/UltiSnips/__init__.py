#!/usr/bin/env python
# encoding: utf-8

import glob
import os
import re
import string
import vim

from UltiSnips.Geometry import Position
from UltiSnips.TextObjects import *
from UltiSnips.Buffer import VimBuffer

class Snippet(object):
    _INDENT = re.compile(r"^[ \t]*")

    def __init__(self,trigger,value, descr):
        self._t = trigger
        self._v = value
        self._d = descr

    def value(self):
        return self._v
    value = property(value)

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
        self._cline = None
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
            self._text_changed = self._cline != vim.current.buffer[line]
        self._lline = self._cline
        self._cline = vim.current.buffer[line]

    def select_span(self, r):
        delta = r.end - r.start
        lineno, col = r.start.line, r.start.col

        vim.current.window.cursor = lineno + 1, col

        if delta.line == delta.col == 0:
            if col == 0 or vim.eval("mode()") != 'i':
                vim.command(r'call feedkeys("\<Esc>i")')
            else:
                vim.command(r'call feedkeys("\<Esc>a")')
        else:
            if delta.line:
                move_lines = "%ij" % delta.line
            else:
                move_lines = ""
            # Depending on the current mode and position, we
            # might need to move escape out of the mode and this
            # will move our cursor one left
            if col != 0 and vim.eval("mode()") == 'i':
                move_one_right = "l"
            else:
                move_one_right = ""

            if 0 <= delta.col <= 1:
                do_select = ""
            elif delta.col > 0:
                do_select = "%il" % (delta.col-1)
            else:
                do_select = "%ih" % (-delta.col+1)


            vim.command(r'call feedkeys("\<Esc>%sv%s%s\<c-g>")' %
                (move_one_right, move_lines, do_select))


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

    def last_line(self):
        return self._lline
    last_line = property(last_line)

class SnippetManager(object):
    def __init__(self):
        self._vstate = VimState()

        self.reset()


    def reset(self):
        self._snippets = {}
        self._csnippets = []
        self._reinit()

    def _reinit(self):
        self._ctab = None
        self._span_selected = None
        self._expect_move_wo_change = False


    def add_snippet(self, trigger, value, descr):
        if "all" not in self._snippets:
            self._snippets["all"] = {}
        l = self._snippets["all"].get(trigger,[])
        l.append(Snippet(trigger,value, descr))
        self._snippets["all"][trigger] = l

    def jump(self, backwards = False):
        if self._cs:
            self._expect_move_wo_change = True
            self._ctab = self._cs.select_next_tab(backwards)
            if self._ctab:
                self._vstate.select_span(self._ctab.abs_span)
                self._span_selected = self._ctab.abs_span
            else:
                # TODO: pop othermost snippet
                self._csnippets.pop()
                if self._cs:
                    self.jump(backwards)
                return True

            self._vstate.update()
            return True
        return False

    def try_expand(self, backwards = False):
        ft = vim.eval("&filetype")
        if len(ft) and ft not in self._snippets:
            self._load_snippets_for(ft)
        if "all" not in self._snippets:
            self._load_snippets_for("all")

        self._expect_move_wo_change = False

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

        if self._cs:
            # Determine position
            pos = self._vstate.pos
            p_start = self._ctab.abs_start

            if pos.line == p_start.line:
                end = Position(0, pos.col - p_start.col)
            else:
                end = Position(pos.line - p_start.line, pos.col)
            start = Position(end.line, end.col - len(snippet.trigger))

            # TODO: very much the same as above
            indent = vim.current.line[:pos.col - len(snippet.trigger)]
            v = snippet.value
            if indent.strip(" \n") == "":
                lines = v.splitlines()
                v = lines[0]
                if len(lines) > 1:
                    v += os.linesep + \
                            os.linesep.join([indent + l for l in lines[1:]])

            # Launch this snippet as a child of the current snippet
            si = SnippetInstance(self._ctab, v, start, end)

            self._update_vim_buffer()

            if si.has_tabs:
                self._csnippets.append(si)
                self._ctab = si.select_next_tab()
                if self._ctab is not None:
                    self._vstate.select_span(self._ctab.abs_span)
                    self._span_selected = self._ctab.abs_span
        else:
            text_before = before.rstrip()[:-len(word)]
            self._vb = VimBuffer(text_before, after)

            start = Position(lineno-1, len(text_before))
            self._csnippets.append(snippet.launch(text_before, start))

            self._vb.replace_lines(lineno-1, lineno-1,
                       self._cs._current_text)

            # TODO: this code is duplicated above
            self._ctab = self._cs.select_next_tab()
            if self._ctab is not None:
                self._vstate.select_span(self._ctab.abs_span)
                self._span_selected = self._ctab.abs_span

        self._vstate.update()

        return True

    def backspace_while_selected(self):
        # BS was called in select mode

        if self._cs and (self._span_selected is not None):
            # This only happens when a default value is delted using backspace
            vim.command(r'call feedkeys("i")')
            self._chars_entered('')
        else:
            vim.command(r'call feedkeys("\<BS>")')

    def _check_if_still_inside_snippet(self):
        # Cursor moved without input.
        self._ctab = None

        # Did we leave the snippet with this movement?
        if self._cs and not (self._vstate.pos in self._cs.abs_span):
            self._csnippets.pop()

            self._reinit()

            self._check_if_still_inside_snippet()

    def cursor_moved(self):
        self._vstate.update()

        if not self._vstate.buf_changed and not self._expect_move_wo_change:
            self._check_if_still_inside_snippet()

        if not self._ctab:
            return

        if self._vstate.buf_changed and self._ctab:
            # Detect a carriage return
            if self._vstate.moved.col <= 0 and self._vstate.moved.line == 1:
                # Multiple things might have happened: either the user entered
                # a newline character or pasted some text which means we have
                # to copy everything he entered on the last line and keep the
                # indent vim chose for this line.
                lline = vim.current.buffer[self._vstate.ppos.line]

                # Another thing that might have happened is that a word
                # wrapped, in this case the last line is shortened and we must
                # delete what vim deleted there
                line_was_shortened = len(self._vstate.last_line) > len(lline)
                user_didnt_enter_newline = len(lline) != self._vstate.ppos.col
                if line_was_shortened and user_didnt_enter_newline:
                    cline = vim.current.buffer[self._vstate.pos.line]
                    self._backspace(len(self._vstate.last_line)-len(lline))
                    self._chars_entered('\n' + cline, 1)
                else:
                    pentered = lline[self._vstate.ppos.col:]
                    this_entered = vim.current.line[:self._vstate.pos.col]

                    self._chars_entered(pentered + '\n' + this_entered)
            elif self._vstate.moved.line == 0 and self._vstate.moved.col<0:
                # Some deleting was going on
                self._backspace(-self._vstate.moved.col)
            elif self._vstate.moved.line < 0:
                # Backspace over line end
                self._backspace(1)
            else:
                line = vim.current.line

                chars = line[self._vstate.pos.col - self._vstate.moved.col:
                             self._vstate.pos.col]
                self._chars_entered(chars)

        self._expect_move_wo_change = False

    def entered_insert_mode(self):
        self._vstate.update()
        if self._cs and self._vstate.has_moved:
            self._reinit()
            self._csnippets = []

    ###################################
    # Private/Protect Functions Below #
    ###################################
    # Input Handling
    def _chars_entered(self, chars, del_more_lines = 0):
        if (self._span_selected is not None):
            self._ctab.current_text = chars

            moved = self._span_selected.start.line - \
                    self._span_selected.end.line
            self._span_selected = None

            self._update_vim_buffer(moved + del_more_lines)
        else:
            self._ctab.current_text += chars
            self._update_vim_buffer(del_more_lines)


    def _backspace(self, count):
        self._ctab.current_text = self._ctab.current_text[:-count]
        self._update_vim_buffer()

    def _update_vim_buffer(self, del_more_lines = 0):
        if not len(self._csnippets):
            return

        s = self._csnippets[0]
        sline = s.abs_start.line
        dlines = s.end.line - s.start.line

        s.update()

        # Replace
        dlines += self._vstate.moved.line + del_more_lines
        self._vb.replace_lines(sline, sline + dlines,
                       s._current_text)
        ct_end = self._ctab.abs_end
        vim.current.window.cursor = ct_end.line +1, ct_end.col

        self._vstate.update()

    def _cs(self):
        if not len(self._csnippets):
            return None
        return self._csnippets[-1]
    _cs = property(_cs)

    # Loading
    def _load_snippets_from(self, ft, fn):
        cs = None
        cv = ""
        cdescr = ""
        for line in open(fn):
            if cs is None and line.startswith("#"):
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
            pattern = p + os.path.sep + "UltiSnips" + os.path.sep + \
                    "*%s.snippets" % ft

            for fn in glob.glob(pattern):
                self._load_snippets_from(ft, fn)



    def _find_snippets(self, ft, trigger):
        snips = self._snippets.get(ft,None)
        if not snips:
            return []

        return snips.get(trigger, [])


UltiSnips_Manager = SnippetManager()

