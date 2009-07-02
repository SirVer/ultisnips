#!/usr/bin/env python
# encoding: utf-8

import vim
import string
import re

def debug(s):
    f = open("/tmp/file.txt","a")
    f.write(s+'\n')
    f.close()

def _replace_text_in_buffer( start, end, textblock ):
    first_line = vim.current.buffer[start.line][:start.col]
    last_line = vim.current.buffer[end.line][end.col:]

    # We do not use splitlines() here because it handles cases like 'text\n'
    # differently than we want it here
    text = textblock.replace('\r','').split('\n')
    if not len(text):
        new_end = Position(start.line, start.col)
        arr = [ first_line + last_line ]
    elif len(text) == 1:
        arr = [ first_line + text[0] + last_line ]
        new_end = Position(start.line, len(arr[0])-len(last_line))
    else:
        arr = [ first_line + text[0] ] + \
                text[1:-1] + \
              [ text[-1] + last_line ]
        new_end = Position(start.line + len(arr)-1, len(arr[-1])-len(last_line))

    vim.current.buffer[start.line:end.line+1] = arr

    return new_end


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
    def __init__(self, parent, start, end):
        self._start = start
        self._end = end
        self._parent = parent

        self._children = []

        if parent is not None:
            parent.add_child(self)

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
    
    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end


class Mirror(TextObject):
    """
    A Mirror object mirrors a TabStop that is, text is repeated here
    """
    def __init__(self, parent, ts, idx, start_col):
        start = Position(idx,start_col)
        end = start + (ts.end - ts.start)
        TextObject.__init__(self, parent, start, end)
        self._tabstop = ts

        ts.add_mirror(self)

    @property
    def tabstop(self):
        return self._tabstop

    def update(self,ts):
        if ts != self._tabstop:
            return 0

        new_end = _replace_text_in_buffer(
            self._parent.start + self._start,
            self._parent.start + self._end,
            self._tabstop.current_text
        )
        new_end -= self._parent.start

        oldcolspan = self.end.col - self.start.col
        oldlinespan = self.end.line - self.start.line
        self._end = new_end
        newcolspan = self.end.col - self.start.col
        newlinespan = self.end.line - self.start.line

        moved_lines = newlinespan - oldlinespan
        moved_cols = newcolspan - oldcolspan

        self._parent._move_textobjects_behind(moved_lines, moved_cols, self)


class TabStop(TextObject):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, parent, idx, span, default_text = ""):
        start = Position(idx,span[0])
        end = Position(idx,span[1])
        TextObject.__init__(self, parent, start, end)

        self._ct = default_text

        self._mirrors = []

    def add_mirror(self, m):
        self._mirrors.append(m)

    def current_text():
        def fget(self):
            return self._ct
        def fset(self, text):
            self._ct = text

            text = text.replace('\r','').split('\n')

            oldlinespan = self.end.line - self.start.line
            oldcolspan  = self.end.col - self.start.col

            new_end = self._start + Position(len(text) - 1, len(text[-1]))

            newlinespan = new_end.line - self.start.line
            newcolspan  = new_end.col - self.start.col

            moved_lines = newlinespan - oldlinespan
            moved_cols = newcolspan - oldcolspan

            self._parent._move_textobjects_behind(moved_lines, moved_cols, self)
            self._end = new_end

            for m in self._mirrors:
                m.update(self)

        return locals()
    current_text = property(**current_text())

    def select(self):
        lineno, col = self._parent.start.line, self._parent.start.col

        newline = lineno + self._start.line
        newcol = self._start.col

        if newline == lineno:
            newcol += col

        vim.current.window.cursor = newline + 1, newcol

        # Select the word
        # Depending on the current mode and position, we
        # might need to move escape out of the mode and this
        # will move our cursor one left
        if len(self._ct) > 0:
            if newcol != 0 and vim.eval("mode()") == 'i':
                move_one_right = "l"
            else:
                move_one_right = ""

            vim.command(r'call feedkeys("\<Esc>%sv%il\<c-g>")'
                % (move_one_right, len(self._ct)-1))


class SnippetInstance(TextObject):
    """
    A Snippet instance is an instance of a Snippet Definition. That is,
    when the user expands a snippet, a SnippetInstance is created to
    keep track of the corresponding TextObjects. The Snippet itself is
    also a TextObject because it has a start an end
    """

    def __init__(self, start, end):
        TextObject.__init__(self, None, start, end)

        self._cts = None
        self._tab_selected = False
        self._tabstops = {}

    def has_tabs(self):
        return len(self._children) > 0

    def add_tabstop(self,no, ts):
        self._tabstops[no] = ts

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

        ts.select()

        self._tab_selected = True
        return True


    def _move_textobjects_behind(self, lines, cols, obj):
        if lines == 0 and cols == 0:
            return

        for m in self._children:
            if m == obj:
                continue

            if m.start.line > obj.end.line:
                m.start.line += lines
                m.end.line += lines
            elif m.start.line == obj.end.line:
                if m.start.col >= obj.end.col:
                    if lines:
                        m.start.line += lines
                        m.end.line += lines
                    else:
                        m.start.col += cols
                        m.end.col += cols


    def backspace(self,count):
        cts = self._tabstops[self._cts]
        cts.current_text = cts.current_text[:-count]

    def chars_entered(self, chars):
        cts = self._tabstops[self._cts]

        if self._tab_selected:
            cts.current_text = chars
            self._tab_selected = False
        else:
            cts.current_text += chars


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

    def _handle_tabstop(self, s, m, val, tabstops):
        no = int(m.group(1))
        def_text = m.group(2)

        start, end = m.span()
        val = val[:start] + def_text + val[end:]

        line_idx = val[:start].count('\n')
        line_start = val[:start].rfind('\n') + 1
        start_in_line = start - line_start
        ts = TabStop(s, line_idx,
                (start_in_line,start_in_line+len(def_text)), def_text)

        tabstops[no] = ts
        s.add_tabstop(no,ts)

        return val

    def _handle_ts_or_mirror(self, s, m, val, tabstops):
        no = int(m.group(3))

        start, end = m.span()

        line_idx = val[:start].count('\n')
        line_start = val[:start].rfind('\n') + 1
        start_in_line = start - line_start

        if no in tabstops:
            m = Mirror(s, tabstops[no], line_idx, start_in_line)
            val = val[:start] + tabstops[no].current_text + val[end:]
        else:
            ts = TabStop(s, line_idx, (start_in_line,start_in_line))
            val = val[:start] + val[end:]
            tabstops[no] = ts
            s.add_tabstop(no,ts)

        return val

    def _find_tabstops(self, s, val):
        tabstops = {}

        while 1:
            m = self._TABSTOP.search(val)

            if m is not None:
                if m.group(1) is not None: # ${1:hallo}
                    val = self._handle_tabstop(s,m,val,tabstops)
                elif m.group(3) is not None: # $1
                    val = self._handle_ts_or_mirror(s,m,val,tabstops)
            else:
                break

        return val

    def launch(self, before, after):
        lineno, col = vim.current.window.cursor
        start = Position(lineno-1,col - len(self._t))
        end = Position(lineno-1,col)

        s = SnippetInstance(start,end)
        text = self._find_tabstops(s, self._v)

        new_end = _replace_text_in_buffer( start, end, text )

        # TODO: hack
        s.end.col = new_end.col
        s.end.line = new_end.line

        if s.has_tabs():
            s.select_next_tab()
            return s
        else:
            vim.current.window.cursor = new_end.line + 1, new_end.col

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
                    cs.chars_entered('\n')
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

