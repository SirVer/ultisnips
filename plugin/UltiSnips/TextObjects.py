#!/usr/bin/env python
# encoding: utf-8

import os
import re
import stat
import tempfile
import vim

from UltiSnips.Buffer import TextBuffer
from UltiSnips.Geometry import Span, Position

__all__ = [ "Mirror", "Transformation", "SnippetInstance", "StartMarker" ]

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
    _CONDITIONAL = re.compile(r"\(\?(\d+):", re.DOTALL)

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

    def _replace_conditional(self, match, v):
        def _find_closingbrace(v,start_pos):
            bracks_open = 1
            for idx, c in enumerate(v[start_pos:]):
                if c == '(':
                    if v[idx+start_pos-1] != '\\':
                        bracks_open += 1
                elif c == ')':
                    if v[idx+start_pos-1] != '\\':
                        bracks_open -= 1
                    if not bracks_open:
                        return start_pos+idx+1
        m = self._CONDITIONAL.search(v)

        def _part_conditional(v):
            bracks_open = 0
            args = []
            carg = ""
            for idx, c in enumerate(v):
                if c == '(':
                    if v[idx-1] != '\\':
                        bracks_open += 1
                elif c == ')':
                    if v[idx-1] != '\\':
                        bracks_open -= 1
                elif c == ':' and not bracks_open and not v[idx-1] == '\\':
                    args.append(carg)
                    carg = ""
                    continue
                carg += c
            args.append(carg)
            return args

        while m:
            start = m.start()
            end = _find_closingbrace(v,start+4)

            args = _part_conditional(v[start+4:end-1])

            rv = ""
            if match.group(int(m.group(1))):
                rv = self._unescape(self._replace_conditional(match,args[0]))
            elif len(args) > 1:
                rv = self._unescape(self._replace_conditional(match,args[1]))

            v = v[:start] + rv + v[end:]

            m = self._CONDITIONAL.search(v)
        return v

    def _unescape(self, v):
        return self._UNESCAPE.subn(lambda m: m.group(0)[-1], v)[0]
    def replace(self, match):
        start, end = match.span()

        tv = self._s

        # Replace all $? with capture groups
        tv = self._DOLLAR.subn(lambda m: match.group(int(m.group(1))), tv)[0]

        # Replace CaseFoldings
        tv = self._SIMPLE_CASEFOLDINGS.subn(self._scase_folding, tv)[0]
        tv = self._LONG_CASEFOLDINGS.subn(self._lcase_folding, tv)[0]
        tv = self._replace_conditional(match, tv)

        return self._unescape(tv.decode("string-escape"))

class _TOParser(object):
    # A simple tabstop with default value
    _TABSTOP = re.compile(r'''(?<!\\)\${(\d+)[:}]''')
    # A mirror or a tabstop without default value.
    _MIRROR_OR_TS = re.compile(r'(?<!\\)\$(\d+)')
    # A mirror or a tabstop without default value.
    _TRANSFORMATION = re.compile(r'(?<!\\)\${(\d+)/(.*?)/(.*?)/([a-zA-z]*)}')
    # The beginning of a shell code fragment
    _SHELLCODE = re.compile(r'(?<!\\)`')
    # The beginning of a python code fragment
    _PYTHONCODE = re.compile(r'(?<!\\)`!p')
    # The beginning of a vimL code fragment
    _VIMCODE = re.compile(r'(?<!\\)`!v')
    # Escaped characters in substrings
    _UNESCAPE = re.compile(r'\\[`$]')

    def __init__(self, parent, val, indent):
        self._v = val
        self._p = parent
        self._indent = indent

        self._childs = []

    def __repr__(self):
        return "TOParser(%s)" % self._p

    def parse(self):
        self._parse_tabs()
        self._parse_pythoncode()
        self._parse_vimlcode()
        self._parse_shellcode()
        self._parse_transformations()
        self._parse_mirrors_or_ts()

        self._parse_escaped_chars()

        self._finish()

    #################
    # Escaped chars #
    #################
    def _parse_escaped_chars(self):
        m = self._UNESCAPE.search(self._v)
        while m:
            self._handle_unescape(m)
            m = self._UNESCAPE.search(self._v)

        for c in self._childs:
            c._parse_escaped_chars()

    def _handle_unescape(self, m):
        start_pos = m.start()
        end_pos = start_pos + 2
        char = self._v[start_pos+1]

        start, end = self._get_start_end(self._v,start_pos,end_pos)

        self._overwrite_area(start_pos,end_pos)

        return EscapedChar(self._p, start, end, char)

    ##############
    # Shell Code #
    ##############
    def _parse_shellcode(self):
        m = self._SHELLCODE.search(self._v)
        while m:
            self._handle_shellcode(m)
            m = self._SHELLCODE.search(self._v)

        for c in self._childs:
            c._parse_shellcode()

    def _handle_shellcode(self, m):
        start_pos = m.start()
        end_pos = self._find_closing_bt(start_pos+1)

        content = self._v[start_pos+1:end_pos-1]

        start, end = self._get_start_end(self._v,start_pos,end_pos)

        self._overwrite_area(start_pos,end_pos)

        return ShellCode(self._p, start, end, content)

    ###############
    # Python Code #
    ###############
    def _parse_pythoncode(self):
        m = self._PYTHONCODE.search(self._v)
        while m:
            self._handle_pythoncode(m)
            m = self._PYTHONCODE.search(self._v)

        for c in self._childs:
            c._parse_pythoncode()

    def _handle_pythoncode(self, m):
        start_pos = m.start()
        end_pos = self._find_closing_bt(start_pos+1)

        # Strip `!p `
        content = self._v[start_pos+3:end_pos-1]

        start, end = self._get_start_end(self._v,start_pos,end_pos)

        self._overwrite_area(start_pos,end_pos)

        # Strip the indent if any
        if len(self._indent):
            lines = content.splitlines()
            new_content = lines[0] + '\n'
            new_content += '\n'.join([l[len(self._indent):]
                        for l in lines[1:]])
        else:
            new_content = content
        new_content = new_content.strip()

        return PythonCode(self._p, start, end, new_content)

    #############
    # VimL Code #
    #############
    def _parse_vimlcode(self):
        m = self._VIMCODE.search(self._v)
        while m:
            self._handle_vimlcode(m)
            m = self._VIMCODE.search(self._v)

        for c in self._childs:
            c._parse_vimlcode()

    def _handle_vimlcode(self, m):
        start_pos = m.start()
        end_pos = self._find_closing_bt(start_pos+1)

        # Strip `!v `
        content = self._v[start_pos+3:end_pos-1]

        start, end = self._get_start_end(self._v,start_pos,end_pos)

        self._overwrite_area(start_pos,end_pos)

        return VimLCode(self._p, start, end, content)



    ########
    # TABS #
    ########
    def _parse_tabs(self):
        ts = []
        m = self._TABSTOP.search(self._v)
        while m:
            ts.append(self._handle_tabstop(m))
            m = self._TABSTOP.search(self._v)

        for t, def_text in ts:
            child_parser = _TOParser(t, def_text, self._indent)
            child_parser._parse_tabs()
            self._childs.append(child_parser)

    def _handle_tabstop(self, m):
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
        end_pos = _find_closingbracket(self._v, start_pos+2)

        def_text = self._v[m.end():end_pos-1]

        start, end = self._get_start_end(self._v,start_pos,end_pos)

        no = int(m.group(1))
        ts = TabStop(no, self._p, start, end, def_text)

        self._p._add_tabstop(no,ts)

        self._overwrite_area(start_pos, end_pos)

        return ts, def_text

    ###################
    # TRANSFORMATIONS #
    ###################
    def _parse_transformations(self):
        self._trans = []
        for m in self._TRANSFORMATION.finditer(self._v):
            self._trans.append(self._handle_transformation(m))

        for t in self._childs:
            t._parse_transformations()

    def _handle_transformation(self, m):
        no = int(m.group(1))
        search = m.group(2)
        replace = m.group(3)
        options = m.group(4)

        start_pos, end_pos = m.span()
        start, end = self._get_start_end(self._v,start_pos,end_pos)

        self._overwrite_area(*m.span())

        return Transformation(self._p, no, start, end, search, replace, options)

    #####################
    # MIRRORS OR TS: $1 #
    #####################
    def _parse_mirrors_or_ts(self):
        for m in self._MIRROR_OR_TS.finditer(self._v):
            self._handle_ts_or_mirror(m)

        for t in self._childs:
            t._parse_mirrors_or_ts()

    def _handle_ts_or_mirror(self, m):
        no = int(m.group(1))

        start_pos, end_pos = m.span()
        start, end = self._get_start_end(self._v,start_pos,end_pos)

        ts = self._p._get_tabstop(self._p, no)
        if ts is not None:
            rv = Mirror(self._p, ts, start, end)
        else:
            rv = TabStop(no, self._p, start, end)
            self._p._add_tabstop(no,rv)

        self._overwrite_area(*m.span())

        return rv

    ###################
    # Resolve symbols #
    ###################
    def _finish(self):
        for c in self._childs:
            c._finish()

        for t in self._trans:
            ts = self._p._get_tabstop(self._p,t._ts)
            if ts is None:
                raise RuntimeError, "Tabstop %i is not known" % t._ts
            t._ts = ts


    ####################
    # Helper functions #
    ####################
    def _find_closing_bt(self, start_pos):
        for idx,c in enumerate(self._v[start_pos:]):
            if c == '`' and self._v[idx+start_pos-1] != '\\':
                return idx + start_pos + 1

    def _get_start_end(self, val, start_pos, end_pos):
        def _get_pos(s, pos):
            line_idx = s[:pos].count('\n')
            line_start = s[:pos].rfind('\n') + 1
            start_in_line = pos - line_start
            return Position(line_idx, start_in_line)

        return _get_pos(val, start_pos), _get_pos(val, end_pos)

    def _overwrite_area(self, s, e):
        """Overwrite the given span with spaces. But keep newlines in place"""
        area = self._v[s:e]
        area = '\n'.join( [" "*len(i) for i in area.splitlines()] )
        self._v = self._v[:s] + area + self._v[e:]



###########################################################################
#                             Public classes                              #
###########################################################################

class TextObject(object):
    """
    This base class represents any object in the text
    that has a span in any ways
    """
    def __init__(self, parent, start, end, initial_text):
        self._start = start
        self._end = end

        self._parent = parent

        self._childs = []
        self._tabstops = {}

        if parent is not None:
            parent._add_child(self)

        self._current_text = TextBuffer(initial_text)

        self._cts = 0

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

            # All our childs are set to "" so they
            # do no longer disturb anything that mirrors it
            for c in self._childs:
                c.current_text = ""
            self._childs = []
            self._tabstops = {}
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
        for idx,c in enumerate(self._childs):
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

    def _get_next_tab(self, no):
        if not len(self._tabstops.keys()):
            return
        tno_max = max(self._tabstops.keys())

        posible_sol = []
        i = no + 1
        while i <= tno_max:
            if i in self._tabstops:
                posible_sol.append( (i, self._tabstops[i]) )
                break
            i += 1

        c = [ c._get_next_tab(no) for c in self._childs ]
        c = filter(lambda i: i, c)

        posible_sol += c

        if not len(posible_sol):
            return None

        return min(posible_sol)


    def _get_prev_tab(self, no):
        if not len(self._tabstops.keys()):
            return
        tno_min = min(self._tabstops.keys())

        posible_sol = []
        i = no - 1
        while i >= tno_min and i > 0:
            if i in self._tabstops:
                posible_sol.append( (i, self._tabstops[i]) )
                break
            i -= 1

        c = [ c._get_prev_tab(no) for c in self._childs ]
        c = filter(lambda i: i, c)

        posible_sol += c

        if not len(posible_sol):
            return None

        return max(posible_sol)


    ###############################
    # Private/Protected functions #
    ###############################
    def _do_update(self):
        pass

    def _move_textobjects_behind(self, start, end, lines, cols, obj_idx):
        if lines == 0 and cols == 0:
            return

        for idx,m in enumerate(self._childs[obj_idx+1:]):
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

    def _get_tabstop(self, requester, no):
        if no in self._tabstops:
            return self._tabstops[no]
        for c in self._childs:
            if c is requester:
                continue

            rv = c._get_tabstop(self, no)
            if rv is not None:
                return rv
        if self._parent and requester is not self._parent:
            return self._parent._get_tabstop(self, no)

    def _add_child(self,c):
        self._childs.append(c)
        self._childs.sort()

    def _add_tabstop(self, no, ts):
        self._tabstops[no] = ts

class EscapedChar(TextObject):
    """
    This class is a escape char like \$. It is handled in a text object
    to make sure that remaining children are correctly moved after
    replacing the text.

    This is a base class without functionality just to mark it in the code.
    """
    pass


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

        self._find = re.compile(s, flags | re.DOTALL)
        self._replace = _CleverReplace(r)

    def _do_update(self):
        t = self._ts.current_text
        t = self._find.subn(self._replace.replace, t, self._match_this_many)[0]
        self.current_text = t

    def __repr__(self):
        return "Transformation(%s -> %s)" % (self._start, self._end)

class ShellCode(TextObject):
    def __init__(self, parent, start, end, code):

        code = code.replace("\\`", "`")

        # Write the code to a temporary file
        handle, path = tempfile.mkstemp(text=True)
        os.write(handle, code)
        os.close(handle)

        os.chmod(path, stat.S_IRWXU)

        # Interpolate the shell code. We try to stay as compatible with Python
        # 2.3, therefore, we do not use the subprocess module here
        output = os.popen(path, "r").read()
        if len(output) and output[-1] == '\n':
            output = output[:-1]
        if len(output) and output[-1] == '\r':
            output = output[:-1]

        os.unlink(path)

        TextObject.__init__(self, parent, start, end, output)

    def __repr__(self):
        return "ShellCode(%s -> %s)" % (self._start, self._end)

class VimLCode(TextObject):
    def __init__(self, parent, start, end, code):
        self._code = code.replace("\\`", "`").strip()

        TextObject.__init__(self, parent, start, end, "")

    def _do_update(self):
        self.current_text = str(vim.eval(self._code))

    def __repr__(self):
        return "VimLCode(%s -> %s)" % (self._start, self._end)

class _Tabs(object):
    def __init__(self, to):
        self._to = to

    def __getitem__(self, no):
        ts = self._to._get_tabstop(self._to, int(no))
        if ts is None:
            return ""
        return ts.current_text

class PythonCode(TextObject):
    def __init__(self, parent, start, end, code):

        code = code.replace("\\`", "`")

        # Add Some convenience to the code
        self._code = "import re, os, vim, string, random\n" + code

        TextObject.__init__(self, parent, start, end, "")

    def _do_update(self):
        path = vim.eval('expand("%")')
        if path is None:
            path = ""
        fn = os.path.basename(path)

        ct = self.current_text
        d = {
            't': _Tabs(self),
            'fn': fn,
            'path': path,
            'cur': ct,
            'res': ct,
        }

        exec self._code in d
        self.current_text = str(d["res"])


    def __repr__(self):
        return "PythonCode(%s -> %s)" % (self._start, self._end)

class TabStop(TextObject):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, no, parent, start, end, default_text = ""):
        TextObject.__init__(self, parent, start, end, default_text)
        self._no = no

    def no(self):
        return self._no
    no = property(no)

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

    # TODO: for beauty sake, start and end should come before initial text
    def __init__(self, parent, indent, initial_text, start = None, end = None):
        if start is None:
            start = Position(0,0)
        if end is None:
            end = Position(0,0)

        TextObject.__init__(self, parent, start, end, initial_text)

        _TOParser(self, initial_text, indent).parse()

        # Check if we have a zero Tab, if not, add one at the end
        if isinstance(parent, TabStop):
            if not parent.no == 0:
                # We are recursively called, if we have a zero tab, remove it.
                if 0 in self._tabstops:
                    self._tabstops[0].current_text = ""
                    del self._tabstops[0]
        else:
            self.update()
            if 0 not in self._tabstops:
                delta = self._end - self._start
                col = self.end.col
                if delta.line == 0:
                    col -= self.start.col
                start = Position(delta.line, col)
                end = Position(delta.line, col)
                ts = TabStop(0, self, start, end, "")
                self._add_tabstop(0,ts)

                self.update()

    def __repr__(self):
        return "SnippetInstance(%s -> %s)" % (self._start, self._end)

    def has_tabs(self):
        return len(self._tabstops)
    has_tabs = property(has_tabs)

    def _get_tabstop(self, requester, no):
        # SnippetInstances are completly self contained,
        # therefore, we do not need to ask our parent
        # for Tabstops
        # TODO: otherwise, this code is identical to
        # TextObject._get_tabstop
        if no in self._tabstops:
            return self._tabstops[no]
        for c in self._childs:
            if c is requester:
                continue

            rv = c._get_tabstop(self, no)
            if rv is not None:
                return rv

    def select_next_tab(self, backwards = False):
        if self._cts is None:
            return

        if backwards:
            cts_bf = self._cts

            res = self._get_prev_tab(self._cts)
            if res is None:
                self._cts = cts_bf
                return self._tabstops[self._cts]
            self._cts, ts = res
            return ts
        else:
            res = self._get_next_tab(self._cts)
            if res is None:
                self._cts = None
                if 0 in self._tabstops:
                    return self._tabstops[0]
                else:
                    return None
            else:
                self._cts, ts = res
                return ts

        return self._tabstops[self._cts]


