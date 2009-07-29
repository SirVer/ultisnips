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

    def __init__(self, trigger, value, descr, options):
        self._t = trigger
        self._v = value
        self._d = descr
        self._opts = options

    def __repr__(self):
        return "Snippet(%s,%s,%s)" % (self._t,self._d,self._opts)

    def overwrites_previous(self):
        return "!" in self._opts
    overwrites_previous = property(overwrites_previous)

    def needs_ws_in_front(self):
        return "b" in self._opts
    needs_ws_in_front = property(needs_ws_in_front)

    def description(self):
        return self._d
    description = property(description)

    def trigger(self):
        return self._t
    trigger = property(trigger)

    def launch(self, text_before, parent, start, end = None):
        indent = self._INDENT.match(text_before).group(0)
        v = self._v
        if len(indent):
            lines = self._v.splitlines()
            v = lines[0]
            if len(lines) > 1:
                v += os.linesep + \
                        os.linesep.join([indent + l for l in lines[1:]])

        if vim.eval("&expandtab") == '1':
            ts = int(vim.eval("&ts"))
            v = v.expandtabs(ts)

        if parent is None:
            return SnippetInstance(StartMarker(start), indent, v)
        else:
            return SnippetInstance(parent, indent, v, start, end)

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
        self._supertab_keys = None

        self.reset()

    def reset(self):
        self._snippets = {}
        self._csnippets = []
        self._reinit()

    def jump_forwards(self):
        if not self._jump():
            return self._handle_failure(self.forward_trigger)

    def jump_backwards(self):
        if not self._jump(True):
            return self._handle_failure(self.backward_trigger)

    def expand(self):
        if not self._try_expand():
            self._handle_failure(self.expand_trigger)

    def expand_or_jump(self):
        """
        This function is used for people who wants to have the same trigger for
        expansion and forward jumping. It first tries to expand a snippet, if
        this fails, it tries to jump forward.
        """
        rv = self._try_expand()
        if not rv:
            rv = self._jump()
        if not rv:
            self._handle_failure(self.expand_trigger)

    def add_snippet(self, trigger, value, descr, options):
        if "all" not in self._snippets:
            self._snippets["all"] = {}
        l = self._snippets["all"].get(trigger,[])
        l.append(Snippet(trigger,value, descr, options))
        self._snippets["all"][trigger] = l


    def backspace_while_selected(self):
        """
        This is called when backspace was used while a placeholder was selected.
        """
        # BS was called in select mode

        if self._cs and (self._span_selected is not None):
            # This only happens when a default value is delted using backspace
            vim.command(r'call feedkeys("i")')
            self._chars_entered('')
        else:
            vim.command(r'call feedkeys("\<BS>")')

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
                # delete what Vim deleted there
                line_was_shortened = len(self._vstate.last_line) > len(lline)

                # Another thing that might have happened is that vim has
                # adjusted the indent of the last line and therefore the line
                # effectivly got longer. This means a newline was entered and
                # we quite definitivly do not want the indent that vim added
                line_was_lengthened = len(lline) > len(self._vstate.last_line)

                user_didnt_enter_newline = len(lline) != self._vstate.ppos.col
                cline = vim.current.buffer[self._vstate.pos.line]
                if line_was_lengthened:
                    this_entered = vim.current.line[:self._vstate.pos.col]
                    self._chars_entered('\n' + cline + this_entered, 1)
                if line_was_shortened and user_didnt_enter_newline:
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
    def _reinit(self):
        self._ctab = None
        self._span_selected = None
        self._expect_move_wo_change = False

    def _check_if_still_inside_snippet(self):
        # Cursor moved without input.
        self._ctab = None

        # Did we leave the snippet with this movement?
        if self._cs and not (self._vstate.pos in self._cs.abs_span):
            self._csnippets.pop()

            self._reinit()

            self._check_if_still_inside_snippet()

    def _jump(self, backwards = False):
        if self._cs:
            self._expect_move_wo_change = True
            self._ctab = self._cs.select_next_tab(backwards)
            if self._ctab:
                self._vstate.select_span(self._ctab.abs_span)
                self._span_selected = self._ctab.abs_span
            else:
                self._csnippets.pop()
                if self._cs:
                    self._jump(backwards)
                return True

            self._vstate.update()
            return True
        return False


    def _handle_failure(self, trigger):
        """
        Mainly make sure that we play well with SuperTab
        """
        feedkey = None
        if not self._supertab_keys:
            if vim.eval("exists('g:SuperTabMappingForward')") != "0":
                self._supertab_keys = (
                    vim.eval("g:SuperTabMappingForward"),
                    vim.eval("g:SuperTabMappingBackward"),
                )
            else:
                self._supertab_keys = [ '', '' ]

        for idx, sttrig in enumerate(self._supertab_keys):
            if trigger.lower() == sttrig.lower():
                if idx == 0:
                    feedkey= r"\<c-n>"
                elif idx == 1:
                    feedkey = r"\<c-p>"
                break

        if feedkey:
            vim.command(r'call feedkeys("%s")' % feedkey)


    def _try_expand(self):
        filetypes = vim.eval("&filetype").split(".") + [ "all" ]
        for ft in filetypes[::-1]:
            if len(ft) and ft not in self._snippets:
                self._load_snippets_for(ft)

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
        found_snippets = []
        for ft in filetypes[::-1]:
            found_snippets += self._find_snippets(ft, word)

        # Search if any of the snippets overwrites the previous
        snippets = []
        for s in found_snippets:
            if s.overwrites_previous:
                snippets = []
            snippets.append(s)

        # Check if there are any only whitespace in front snippets
        text_before = before.rstrip()[:-len(word)]
        if text_before.strip(" \t") != '':
            snippets = [ s for s in snippets if not s.needs_ws_in_front ]

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

            si = snippet.launch(text_before, self._ctab, start, end)

            self._update_vim_buffer()

            if si.has_tabs:
                self._csnippets.append(si)
                self._jump()
        else:
            self._vb = VimBuffer(text_before, after)

            start = Position(lineno-1, len(text_before))
            self._csnippets.append(snippet.launch(text_before, None, start))

            self._vb.replace_lines(lineno-1, lineno-1,
                       self._cs._current_text)

            self._jump()

        return True


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
        coptions = ""
        for line in open(fn):
            if cs is None and line.startswith("#"):
                continue
            if line.startswith("snippet"):
                cs = line.split()[1]
                left = line.find('"')
                if left != -1:
                    right = line.rfind('"')
                    cdescr = line[left+1:right]
                    coptions = line[right:].strip()
                continue
            if cs != None:
                if line.startswith("endsnippet"):
                    cv = cv[:-1] # Chop the last newline
                    l = self._snippets[ft].get(cs,[])
                    l.append(Snippet(cs,cv,cdescr,coptions))
                    self._snippets[ft][cs] = l
                    cv = cdescr = coptions = ""
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

