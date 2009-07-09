#!/usr/bin/env python
# encoding: utf-8

import re

from PySnipEmu.Buffer import TextBuffer
from PySnipEmu.Geometry import Span, Position

__all__ = [ "Mirror", "Transformation", "SnippetInstance", "StartMarker" ]

from PySnipEmu.debug import debug

###########################################################################
#                              Helper class                               #
###########################################################################
class _CleverReplace(object):
    """
    This class mimics TextMates replace syntax
    """
    _DOLLAR = re.compile(r"\$(\d+)", re.DOTALL)
    _SIMPLE_CASEFOLDINGS = re.compile(r"\\([ul].)", re.DOTALL)
    _LONG_CASEFOLDINGS = re.compile(r"\\([UL].*?)\\E", re.DOTALL)
    _CONDITIONAL = re.compile(r"\(\?(\d+):(.*?)(?<!\\)\)", re.DOTALL)

    _UNESCAPE = re.compile(r'\\[^ntrab]')

    def __init__(self, s):
        self._s = s

    def _scase_folding(self, m):
        if m.group(1)[0] == 'u':
            return m.group(1)[-1].upper()
        else:
            return m.group(1)[-1].lower()
    def _lcase_folding(self, m):
        if m.group(1)[0] == 'U':
            return m.group(1)[1:].upper()
        else:
            return m.group(1)[1:].lower()

    def _unescape(self, v):
        return self._UNESCAPE.subn(lambda m: m.group(0)[-1], v)[0]
    def replace(self, match):
        start, end = match.span()

        tv = self._s

        # Replace all $? with capture groups
        tv = self._DOLLAR.subn(lambda m: match.group(int(m.group(1))), tv)[0]

        def _conditional(m):
            args = m.group(2).split(':')
            # TODO: the returned string should be checked for conditionals
            if match.group(int(m.group(1))):
                return self._unescape(args[0])
            elif len(args) > 1:
                return self._unescape(args[1])
            else:
                return ""

        # Replace CaseFoldings
        tv = self._SIMPLE_CASEFOLDINGS.subn(self._scase_folding, tv)[0]
        tv = self._LONG_CASEFOLDINGS.subn(self._lcase_folding, tv)[0]
        tv = self._CONDITIONAL.subn(_conditional, tv)[0]

        rv = tv.decode("string-escape")

        return rv

###########################################################################
#                             Public classes                              #
###########################################################################
class TextObject(object):
    """
    This base class represents any object in the text
    that has a span in any ways
    """
    # A simple tabstop with default value
    _TABSTOP = re.compile(r'''\${(\d+)[:}]''')
    # A mirror or a tabstop without default value.
    _MIRROR_OR_TS = re.compile(r'\$(\d+)')
    # A mirror or a tabstop without default value.
    _TRANSFORMATION = re.compile(r'\${(\d+)/(.*?)/(.*?)/([a-zA-z]*)}')

    def __init__(self, parent, start, end, initial_text):
        self._start = start
        self._end = end

        self._parent = parent

        self._children = []
        self._tabstops = {}

        if parent is not None:
            parent._add_child(self)

        self._has_parsed = False

        self._current_text = initial_text

    def __cmp__(self, other):
        return cmp(self._start, other._start)


    ##############
    # PROPERTIES #
    ##############
    def current_text():
        def fget(self):
            return str(self._current_text)
        def fset(self, text):
            self._current_text = TextBuffer(text)

            # Now, we can have no more childen
            self._children = []
        return locals()

    current_text = property(**current_text())
    def abs_start(self):
        if self._parent:
            ps = self._parent.abs_start
            if self._start.line == 0:
                return ps + self._start
            else:
                return Position(ps.line + self._start.line, self._start.col)
        return self._start
    abs_start = property(abs_start)

    def abs_end(self):
        if self._parent:
            ps = self._parent.abs_start
            if self._end.line == 0:
                return ps + self._end
            else:
                return Position(ps.line + self._end.line, self._end.col)

        return self._end
    abs_end = property(abs_end)

    def span(self):
        return Span(self._start, self._end)
    span = property(span)

    def start(self):
        return self._start
    start = property(start)

    def end(self):
        return self._end
    end = property(end)

    def abs_span(self):
        return Span(self.abs_start, self.abs_end)
    abs_span = property(abs_span)

    ####################
    # Public functions #
    ####################
    def update(self):
        if not self._has_parsed:
            self._current_text = TextBuffer(self._parse(self._current_text))

        for idx,c in enumerate(self._children):
            oldend = Position(c.end.line, c.end.col)

            new_end = c.update()

            moved_lines = new_end.line - oldend.line
            moved_cols = new_end.col - oldend.col

            self._current_text.replace_text(c.start, oldend, c._current_text)

            self._move_textobjects_behind(c.start, oldend, moved_lines,
                        moved_cols, idx)

        self._do_update()

        new_end = self._current_text.calc_end(self._start)

        self._end = new_end

        return new_end

    ###############################
    # Private/Protected functions #
    ###############################
    def _do_update(self):
        pass

    def _move_textobjects_behind(self, start, end, lines, cols, obj_idx):
        if lines == 0 and cols == 0:
            return

        for idx,m in enumerate(self._children[obj_idx+1:]):
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

    def _get_tabstop(self,no):
        if no in self._tabstops:
            return self._tabstops[no]
        if self._parent:
            return self._parent._get_tabstop(no)

    def _add_child(self,c):
        self._children.append(c)
        self._children.sort()

    def _add_tabstop(self, no, ts):
        self._tabstops[no] = ts



    # Parsing below
    def _get_start_end(self, val, start_pos, end_pos):
        def _get_pos(s, pos):
            line_idx = s[:pos].count('\n')
            line_start = s[:pos].rfind('\n') + 1
            start_in_line = pos - line_start
            return Position(line_idx, start_in_line)

        return _get_pos(val, start_pos), _get_pos(val, end_pos)

    def _handle_tabstop(self, m, val):
        def _find_closingbracket(v,start_pos):
            bracks_open = 1
            for idx, c in enumerate(v[start_pos:]):
                if c == '{':
                    if v[idx+start_pos-1] != '\\':
                        bracks_open += 1
                elif c == '}':
                    if v[idx+start_pos-1] != '\\':
                        bracks_open -= 1
                    if not bracks_open:
                        return start_pos+idx+1

        start_pos = m.start()
        end_pos = _find_closingbracket(val, start_pos+2)

        def_text = val[m.end():end_pos-1]

        start, end = self._get_start_end(val,start_pos,end_pos)

        ts = TabStop(self, start, end, def_text)

        self._add_tabstop(int(m.group(1)),ts)

        return val[:start_pos] + (end_pos-start_pos)*" " + val[end_pos:]


    def _handle_ts_or_mirror(self, m, val):
        no = int(m.group(1))

        start_pos, end_pos = m.span()
        start, end = self._get_start_end(val,start_pos,end_pos)

        ts = self._get_tabstop(no)
        if ts is not None:
            Mirror(self, ts, start, end)
        else:
            ts = TabStop(self, start, end)
            self._add_tabstop(no,ts)

    def _handle_transformation(self, m, val):
        no = int(m.group(1))
        search = m.group(2)
        replace = m.group(3)
        options = m.group(4)

        start_pos, end_pos = m.span()
        start, end = self._get_start_end(val,start_pos,end_pos)

        Transformation(self, no, start, end, search, replace, options)


    def _parse(self, val):
        self._has_parsed = True

        if not len(val):
            return val

        for m in self._TABSTOP.finditer(val):
            val = self._handle_tabstop(m,val)

        for m in self._TRANSFORMATION.finditer(val):
            self._handle_transformation(m,val)
            # Replace the whole definition with spaces
            s, e = m.span()
            val = val[:s] + (e-s)*" " + val[e:]


        for m in self._MIRROR_OR_TS.finditer(val):
            self._handle_ts_or_mirror(m,val)
            # Replace the whole definition with spaces
            s, e = m.span()
            val = val[:s] + (e-s)*" " + val[e:]

        return val

class StartMarker(TextObject):
    """
    This class only remembers it's starting position. It is used to
    transform relative values into absolute position values in the vim
    buffer
    """
    def __init__(self, start):
        end = Position(start.line, start.col)
        TextObject.__init__(self, None, start, end, "")


class Mirror(TextObject):
    """
    A Mirror object mirrors a TabStop that is, text is repeated here
    """
    def __init__(self, parent, ts, start, end):
        TextObject.__init__(self, parent, start, end, "")

        self._ts = ts

    def _do_update(self):
        self.current_text = self._ts.current_text

    def __repr__(self):
        return "Mirror(%s -> %s)" % (self._start, self._end)


class Transformation(Mirror):
    def __init__(self, parent, ts, start, end, s, r, options):
        Mirror.__init__(self, parent, ts, start, end)

        flags = 0
        self._match_this_many = 1
        if options:
            if "g" in options:
                self._match_this_many = 0
            if "i" in options:
                flags |=  re.IGNORECASE

        self._find = re.compile(s, flags)
        self._replace = _CleverReplace(r)

    def _do_update(self):
        if isinstance(self._ts,int):
            self._ts = self._parent._get_tabstop(self._ts)

        t = self._ts.current_text
        t = self._find.subn(self._replace.replace, t, self._match_this_many)[0]
        self.current_text = t

    def __repr__(self):
        return "Transformation(%s -> %s)" % (self._start, self._end)


class TabStop(TextObject):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, parent, start, end, default_text = ""):
        TextObject.__init__(self, parent, start, end, default_text)

    def __repr__(self):
        return "TabStop(%s -> %s, %s)" % (self._start, self._end,
            repr(self._current_text))

class SnippetInstance(TextObject):
    """
    A Snippet instance is an instance of a Snippet Definition. That is,
    when the user expands a snippet, a SnippetInstance is created to
    keep track of the corresponding TextObjects. The Snippet itself is
    also a TextObject because it has a start an end
    """

    def __init__(self, parent, initial_text):
        start = Position(0,0)
        end = Position(0,0)
        TextObject.__init__(self, parent, start, end, "")
        self._current_text = TextBuffer(self._parse(initial_text))

        self._end = self._current_text.calc_end(start)

        self._cts = None

        TextObject.update(self)

        # Check if we have a zero Tab, if not, add one at the end
        if 0 not in self._tabstops:
            delta = self._end - self._start
            col = self.end.col
            if delta.line == 0:
                col -= self.start.col
            start = Position(delta.line, col)
            end = Position(delta.line, col)
            ts = TabStop(self, start, end, "")
            self._add_tabstop(0,ts)

            TextObject.update(self)

    def __repr__(self):
        return "SnippetInstance(%s -> %s)" % (self._start, self._end)

    def select_next_tab(self, backwards = False):
        if self._cts == 0:
            return None

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
                    return None

        return self._tabstops[self._cts]

