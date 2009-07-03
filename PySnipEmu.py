#!/usr/bin/env python
# encoding: utf-8

import vim
import string
import re

def debug(s):
    f = open("/tmp/file.txt","a")
    f.write(s+'\n')
    f.close()

class Buffer(object):
    def _replace(self, start, end, content, first_line, last_line):

        text = content[:]
        if len(text) == 1:
            arr = [ first_line + text[0] + last_line ]
            new_end = start + Position(0,len(text[0]))
        else:
            arr = [ first_line + text[0] ] + \
                    text[1:-1] + \
                    [ text[-1] + last_line ]
            new_end = Position(start.line + len(text)-1, len(text[-1]))

        self[start.line:end.line+1] = arr

        return new_end

class TextBuffer(Buffer):
    def __init__(self, textblock):
        # We do not use splitlines() here because it handles cases like 'text\n'
        # differently than we want it here
        self._lines = textblock.replace('\r','').split('\n')

    def calc_end(self, start):
        text = self._lines[:]
        if len(text) == 1:
            new_end = start + Position(0,len(text[0]))
        else:
            new_end = Position(start.line + len(text)-1, len(text[-1]))
        return new_end

    def replace_text( self, start, end, content ):
        first_line = self[start.line][:start.col]
        last_line = self[end.line][end.col:]
        return self._replace( start, end, content, first_line, last_line)

    def __getitem__(self, a):
        return self._lines.__getitem__(a)
    def __setitem__(self, a, b):
        return self._lines.__setitem__(a,b)
    def __repr__(self):
        return repr('\n'.join(self._lines))
    def __str__(self):
        return '\n'.join(self._lines)

class VimBuffer(Buffer):
    def __init__(self, before, after):
        self._bf = before
        self._af = after
    def __getitem__(self, a):
        return vim.current.buffer[a]
    def __setitem__(self, a, b):
        if isinstance(a,slice):
            vim.current.buffer[a.start:a.stop] = b
        else:
            vim.current.buffer[a] = b
    def __repr__(self):
        return "VimBuffer()"

    def replace_text( self, start, end, content ):
        return self._replace( start, end, content, self._bf, self._af)

class Position(object):
    def __init__(self, line, col):
        self.line = line
        self.col = col

    def col():
        def fget(self):
            return self._col
        def fset(self, value):
            if value < 0:
                raise RuntimeError, "Invalid Column: %i" % col
            self._col = value
        return locals()
    col = property(**col())

    def line():
        doc = "Zero base line numbers"
        def fget(self):
            return self._line
        def fset(self, value):
            if value < 0:
                raise RuntimeError, "Invalid Line: %i" % line
            self._line = value
        return locals()
    line = property(**line())

    def __add__(self,pos):
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))

        return Position(self.line + pos.line, self.col + pos.col)

    def __sub__(self,pos):
        if not isinstance(pos,Position):
            raise TypeError("unsupported operand type(s) for +: " \
                    "'Position' and %s" % type(pos))

        return Position(self.line - pos.line, self.col - pos.col)

    def __repr__(self):
        return "(%i,%i)" % (self._line, self._col)

class TextObject(object):
    """
    This base class represents any object in the text
    that has a span in any ways
    """
    # A simple tabstop with default value
    _TABSTOP = re.compile(r'''\${(\d+):(.*?)}''')
    # A mirror or a tabstop without default value.
    _MIRROR_OR_TS = re.compile(r'\$(\d+)')

    def __init__(self, parent, start, end, initial_text):
        self._start = start
        self._end = end

        self._parent = parent

        self._children = []
        self._tabstops = {}

        if parent is not None:
            parent.add_child(self)

        self._has_parsed = False

        self._current_text = initial_text

        debug("New text_object: %s" % self)
        if len(self._children):
            debug("  Children:")
            for c in self._children:
                debug("  %s" % c)

    def _do_update(self):
        pass

    def update(self, change_buffer, indend = ""):
        if not self._has_parsed:
            self._current_text = TextBuffer(self._parse(self._current_text))

        debug("%sUpdating %s" % (indend, self))
        for c in self._children:
            debug("%s   Updating Child%s" % (indend, c))
            oldend = Position(c.end.line, c.end.col)

            moved_lines, moved_cols = c.update( self._current_text, indend + ' '*8 )
            self._move_textobjects_behind(oldend, moved_lines, moved_cols, c)

            debug("%s     Moved%i, %i" % (indend, moved_lines, moved_cols))
            debug("%s     Our text is now: %s" % (indend, repr(self._current_text)))

        debug("%s  self._current_text: %s" % (indend, repr(self._current_text)))

        self._do_update()

        new_end = change_buffer.replace_text(self.start, self.end, self._current_text)

        moved_lines = new_end.line - self._end.line
        moved_cols = new_end.col - self._end.col

        self._end = new_end
        debug("%s  new_end: %s" % (indend, new_end))

        return moved_lines, moved_cols



    def _move_textobjects_behind(self, end, lines, cols, obj):
        if lines == 0 and cols == 0:
            return

        debug("_move_textobjects_behind: %s" % end)
        for m in self._children:
            if m == obj:
                continue


            delta_lines = 0
            delta_cols_begin = 0
            delta_cols_end = 0

            if m.start.line > end.line:
                delta_lines = lines
            elif m.start.line == end.line:
                if m.start.col >= end.col:
                    if lines:
                        delta_lines = lines
                    delta_cols_begin = cols
                    if m.start.line == m.end.line:
                        delta_cols_end = cols

            m.start.line += delta_lines
            m.end.line += delta_lines
            m.start.col += delta_cols_begin
            m.end.col += delta_cols_end

    def _get_start_end(self, val, start_pos, end_pos):
        def _get_pos(s, pos):
            line_idx = s[:pos].count('\n')
            line_start = s[:pos].rfind('\n') + 1
            start_in_line = pos - line_start
            return Position(line_idx, start_in_line)

        return _get_pos(val, start_pos), _get_pos(val, end_pos)


    def _handle_tabstop(self, m, val):
        no = int(m.group(1))
        def_text = m.group(2)

        start_pos, end_pos = m.span()
        start, end = self._get_start_end(val,start_pos,end_pos)

        ts = TabStop(self, start, end, def_text)

        self.add_tabstop(no,ts)

    def _get_tabstop(self,no):
        if no in self._tabstops:
            return self._tabstops[no]
        if self._parent:
            return self._parent._get_tabstop(no)

    def _handle_ts_or_mirror(self, m, val):
        no = int(m.group(1))

        start_pos, end_pos = m.span()
        start, end = self._get_start_end(val,start_pos,end_pos)

        ts = self._get_tabstop(no)
        if ts is not None:
            m = Mirror(self, ts, start, end)
        else:
            ts = TabStop(self, start, end)
            self.add_tabstop(no,ts)

    def add_tabstop(self,no, ts):
        self._tabstops[no] = ts

    def _parse(self, val):
        self._has_parsed = True

        if not len(val):
            return val

        for m in self._TABSTOP.finditer(val):
            self._handle_tabstop(m,val)
            # Replace the whole definition with spaces
            s, e = m.span()
            val = val[:s] + (e-s)*" " + val[e:]
            debug("Handled a tabstop: %s" % repr(val))

        for m in self._MIRROR_OR_TS.finditer(val):
            self._handle_ts_or_mirror(m,val)
            # Replace the whole definition with spaces
            s, e = m.span()
            val = val[:s] + (e-s)*" " + val[e:]
            debug("Handled a mirror or ts: %s" % repr(val))

        debug("End of parse: %s" % repr(val))

        return val

    def add_child(self,c):
        self._children.append(c)

    def parent():
        doc = "The parent TextObject this TextObject resides in"
        def fget(self):
            return self._parent
        def fset(self, value):
            self._parent = value
        return locals()
    parent = property(**parent())

    def start(self):
        return self._start
    start = property(start)

    def end(self):
        return self._end
    end = property(end)

class ChangeableText(TextObject):
    def __init__(self, parent, start, end, initial = ""):
        TextObject.__init__(self, parent, start, end, initial)

    def _set_text(self, text):
        debug("_set_text: %s" % repr(text))
        self._current_text = TextBuffer(text)

        # Now, we can have no more childen
        self._children = []

    def current_text():
        def fget(self):
            return str(self._current_text)
        def fset(self, text):
            self._set_text(text)
        return locals()
    current_text = property(**current_text())


class Mirror(ChangeableText):
    """
    A Mirror object mirrors a TabStop that is, text is repeated here
    """
    def __init__(self, parent, ts, start, end):
        ChangeableText.__init__(self, parent, start, end)

        self._ts = ts

    def _do_update(self):
        debug("In Mirror: %s %s" % (repr(self.current_text),repr(self._ts.current_text)))
        self.current_text = self._ts.current_text

    def __repr__(self):
        return "Mirror(%s -> %s)" % (self._start, self._end)


class TabStop(ChangeableText):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, parent, start, end, default_text = ""):
        ChangeableText.__init__(self, parent, start, end, default_text)

    def __repr__(self):
        return "TabStop(%s -> %s, %s)" % (self._start, self._end,
            repr(self._current_text))

    def select(self, start):
        lineno, col = start.line, start.col

        newline = lineno + self._start.line
        newcol = self._start.col

        if newline == lineno:
            newcol += col

        vim.current.window.cursor = newline + 1, newcol

        if len(self.current_text) > 0:
            # Select the word
            # Depending on the current mode and position, we
            # might need to move escape out of the mode and this
            # will move our cursor one left
            if newcol != 0 and vim.eval("mode()") == 'i':
                move_one_right = "l"
            else:
                move_one_right = ""

            if len(self.current_text) == 1:
                do_select = ""
            else:
                do_select = "%il" % (len(self.current_text)-1)

            vim.command(r'call feedkeys("\<Esc>%sv%s\<c-g>")' %
                (move_one_right, do_select))


class SnippetInstance(TextObject):
    """
    A Snippet instance is an instance of a Snippet Definition. That is,
    when the user expands a snippet, a SnippetInstance is created to
    keep track of the corresponding TextObjects. The Snippet itself is
    also a TextObject because it has a start an end
    """

    def __init__(self, start, end, initial_text, text_before, text_after):
        TextObject.__init__(self, None, start, end, initial_text)

        self._cts = None
        self._tab_selected = False

        self._vb = VimBuffer(text_before, text_after)

        self._current_text = TextBuffer(self._parse(initial_text))

        debug("Before update!");
        self.update(self._vb)
        debug("After update!");


    def has_tabs(self):
        return len(self._children) > 0


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

        ts.select(self._start)

        self._tab_selected = True
        return True

    def backspace(self,count):
        cts = self._tabstops[self._cts]
        cts.current_text = cts.current_text[:-count]

        self.update(self._vb)

    def chars_entered(self, chars):
        cts = self._tabstops[self._cts]

        if self._tab_selected:
            cts.current_text = chars
            self._tab_selected = False
        else:
            cts.current_text += chars

        self.update(self._vb)


class Snippet(object):
    def __init__(self,trigger,value):
        self._t = trigger
        self._v = value

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

        s = SnippetInstance(start, end, self._v, text_before, text_after)

        if s.has_tabs():
            s.select_next_tab()
            return s
        else:
            vim.current.window.cursor = s.end.line + 1, s.end.col

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
            if lineno in \
                [ self._last_cursor_pos[0], self._last_cursor_pos[0]+1]:
                cs = self._current_snippets[-1]

                # Detect a carriage return
                if col == 0 and lineno == self._last_cursor_pos[0] + 1:
                    # Hack, remove a line in vim, because we are going to
                    # overwrite the old line range with the new snippet value.
                    # After the expansion, we put the cursor were the user left
                    # it. This action should be completely transparent for the
                    # user
                    cache_pos = vim.current.window.cursor
                    del vim.current.buffer[lineno-1]
                    cs.chars_entered('\n')
                    vim.current.window.cursor = cache_pos
                elif lcol > col: # Some deleting was going on
                    cs.backspace(lcol-col)
                else:
                    line = vim.current.line

                    chars = line[lcol:col]
                    cs.chars_entered(chars)

        self._last_cursor_pos = cp

    def entered_insert_mode(self):
        pass

PySnipSnippets = SnippetManager()

