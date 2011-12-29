#!/usr/bin/env python
# encoding: utf-8

import os
import re
import stat
import tempfile
import vim

from UltiSnips.Util import IndentUtil
from UltiSnips.Buffer import TextBuffer
from UltiSnips.Geometry import Span, Position
from UltiSnips.Lexer import tokenize, EscapeCharToken, TransformationToken,  \
    TabStopToken, MirrorToken, PythonCodeToken, VimLCodeToken, ShellCodeToken

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
    def __init__(self, parent_to, text, indent):
        self._indent = indent
        self._parent_to = parent_to
        self._text = text

    def parse(self):
        seen_ts = {}
        all_tokens = []

        self._do_parse(all_tokens, seen_ts)

        self._resolve_ambiguity(all_tokens, seen_ts)
        self._create_objects_with_links_to_tabs(all_tokens, seen_ts)

    #####################
    # Private Functions #
    #####################
    def _resolve_ambiguity(self, all_tokens, seen_ts):
        for parent, token in all_tokens:
            if isinstance(token, MirrorToken):
                if token.no not in seen_ts:
                    ts = TabStop(parent, token)
                    seen_ts[token.no] = ts
                    parent._add_tabstop(token.no,ts)
                else:
                    Mirror(parent, seen_ts[token.no], token)

    def _create_objects_with_links_to_tabs(self, all_tokens, seen_ts):
        for parent, token in all_tokens:
            if isinstance(token, TransformationToken):
                if token.no not in seen_ts:
                    raise RuntimeError("Tabstop %i is not known but is used by a Transformation" % t._ts)
                Transformation(parent, seen_ts[token.no], token)

    def _do_parse(self, all_tokens, seen_ts):
        tokens = list(tokenize(self._text, self._indent))

        for token in tokens:
            all_tokens.append((self._parent_to, token))

            if isinstance(token, TabStopToken):
                ts = TabStop(self._parent_to, token)
                seen_ts[token.no] = ts
                self._parent_to._add_tabstop(token.no,ts)

                k = _TOParser(ts, ts.current_text, self._indent)
                k._do_parse(all_tokens, seen_ts)
            elif isinstance(token, EscapeCharToken):
                EscapedChar(self._parent_to, token)
            elif isinstance(token, ShellCodeToken):
                ShellCode(self._parent_to, token)
            elif isinstance(token, PythonCodeToken):
                PythonCode(self._parent_to, token)
            elif isinstance(token, VimLCodeToken):
                VimLCode(self._parent_to, token)



###########################################################################
#                             Public classes                              #
###########################################################################
class TextObject(object):
    """
    This base class represents any object in the text
    that has a span in any ways
    """
    def __init__(self, parent, token, end = None, initial_text = ""):
        self._parent = parent

        if end is not None: # Took 4 arguments
            self._start = token
            self._end = end
            self._current_text = TextBuffer(initial_text)
        else: # Initialize from token
            self._start = token.start
            self._end = token.end
            self._current_text = TextBuffer(token.initial_text)

        self._childs = []
        self._tabstops = {}

        if parent is not None:
            parent._add_child(self)

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
        def _update_childs(childs):
            for idx,c in childs:
                oldend = Position(c.end.line, c.end.col)

                new_end = c.update()

                moved_lines = new_end.line - oldend.line
                moved_cols = new_end.col - oldend.col

                self._current_text.replace_text(c.start, oldend, c._current_text)

                self._move_textobjects_behind(c.start, oldend, moved_lines,
                            moved_cols, idx)

        _update_childs((idx, c) for idx, c in enumerate(self._childs) if isinstance(c, TabStop))
        _update_childs((idx, c) for idx, c in enumerate(self._childs) if not isinstance(c, TabStop))

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
        TextObject.__init__(self, None, start, end)


class Mirror(TextObject):
    """
    A Mirror object mirrors a TabStop that is, text is repeated here
    """
    def __init__(self, parent, ts, token):
        TextObject.__init__(self, parent, token)

        self._ts = ts

    def _do_update(self):
        self.current_text = self._ts.current_text

    def __repr__(self):
        return "Mirror(%s -> %s)" % (self._start, self._end)


class Transformation(Mirror):
    def __init__(self, parent, ts, token):
        Mirror.__init__(self, parent, ts, token)

        flags = 0
        self._match_this_many = 1
        if token.options:
            if "g" in token.options:
                self._match_this_many = 0
            if "i" in token.options:
                flags |=  re.IGNORECASE

        self._find = re.compile(token.search, flags | re.DOTALL)
        self._replace = _CleverReplace(token.replace)

    def _do_update(self):
        t = self._ts.current_text
        t = self._find.subn(self._replace.replace, t, self._match_this_many)[0]
        self.current_text = t

    def __repr__(self):
        return "Transformation(%s -> %s)" % (self._start, self._end)

class ShellCode(TextObject):
    def __init__(self, parent, token):
        code = token.code.replace("\\`", "`")

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

        token.initial_text = output
        TextObject.__init__(self, parent, token)

    def __repr__(self):
        return "ShellCode(%s -> %s)" % (self._start, self._end)

class VimLCode(TextObject):
    def __init__(self, parent, token):
        self._code = token.code.replace("\\`", "`").strip()

        TextObject.__init__(self, parent, token)

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

class SnippetUtil(object):
    """ Provides easy access to indentation, etc.
    """

    def __init__(self, initial_indent, cur=""):
        self._ind = IndentUtil()

        self._initial_indent = self._ind.indent_to_spaces(initial_indent)

        self._reset(cur)

    def _reset(self, cur):
        """ Gets the snippet ready for another update.

        :cur: the new value for c.
        """
        self._ind.reset()
        self._c = cur
        self._rv = ""
        self._changed = False
        self.reset_indent()

    def shift(self, amount=1):
        """ Shifts the indentation level.
        Note that this uses the shiftwidth because thats what code
        formatters use.

        :amount: the amount by which to shift.
        """
        self.indent += " " * self._ind.sw * amount

    def unshift(self, amount=1):
        """ Unshift the indentation level.
        Note that this uses the shiftwidth because thats what code
        formatters use.

        :amount: the amount by which to unshift.
        """
        by = -self._ind.sw * amount
        try:
            self.indent = self.indent[:by]
        except IndexError:
            indent = ""

    def mkline(self, line="", indent=None):
        """ Creates a properly set up line.

        :line: the text to add
        :indent: the indentation to have at the beginning
                 if None, it uses the default amount
        """
        if indent == None:
            indent = self.indent
            # this deals with the fact that the first line is
            # already properly indented
            if '\n' not in self._rv:
                try:
                    indent = indent[len(self._initial_indent):]
                except IndexError:
                    indent = ""
            indent = self._ind.spaces_to_indent(indent)

        return indent + line

    def reset_indent(self):
        """ Clears the indentation. """
        self.indent = self._initial_indent

    # Utility methods
    @property
    def fn(self):
        """ The filename. """
        return vim.eval('expand("%:t")') or ""

    @property
    def basename(self):
        """ The filename without extension. """
        return vim.eval('expand("%:t:r")') or ""

    @property
    def ft(self):
        """ The filetype. """
        return self.opt("&filetype", "")

    # Necessary stuff
    def rv():
        """ The return value.
        This is a list of lines to insert at the
        location of the placeholder.

        Deprecates res.
        """
        def fget(self):
            return self._rv
        def fset(self, value):
            self._changed = True
            self._rv = value
        return locals()
    rv = property(**rv())

    @property
    def _rv_changed(self):
        """ True if rv has changed. """
        return self._changed

    @property
    def c(self):
        """ The current text of the placeholder.

        Deprecates cur.
        """
        return self._c

    def opt(self, option, default=None):
        """ Gets a vim variable. """
        if vim.eval("exists('%s')" % option) == "1":
            try:
                return vim.eval(option)
            except vim.error:
                pass
        return default

    # Syntatic sugar
    def __add__(self, value):
        """ Appends the given line to rv using mkline. """
        self.rv += '\n' # handles the first line properly
        self.rv += self.mkline(value)
        return self

    def __lshift__(self, other):
        """ Same as unshift. """
        self.unshift(other)

    def __rshift__(self, other):
        """ Same as shift. """
        self.shift(other)


class PythonCode(TextObject):
    def __init__(self, parent, token):

        code = token.code.replace("\\`", "`")

        # Find our containing snippet for snippet local data
        snippet = parent
        while snippet and not isinstance(snippet, SnippetInstance):
            try:
                snippet = snippet._parent
            except AttributeError:
                snippet = None
        self._snip = SnippetUtil(token.indent)
        self._locals = snippet.locals

        self._globals = {}
        globals = snippet.globals.get("!p", [])
        exec "\n".join(globals).replace("\r\n", "\n") in self._globals

        # Add Some convenience to the code
        self._code = "import re, os, vim, string, random\n" + code

        TextObject.__init__(self, parent, token)


    def _do_update(self):
        path = vim.eval('expand("%")')
        if path is None:
            path = ""
        fn = os.path.basename(path)

        ct = self.current_text
        self._snip._reset(ct)
        local_d = self._locals

        local_d.update({
            't': _Tabs(self),
            'fn': fn,
            'path': path,
            'cur': ct,
            'res': ct,
            'snip' : self._snip,
        })

        self._code = self._code.replace("\r\n", "\n")
        exec self._code in self._globals, local_d

        if self._snip._rv_changed:
            self.current_text = self._snip.rv
        else:
            self.current_text = str(local_d["res"])

    def __repr__(self):
        return "PythonCode(%s -> %s)" % (self._start, self._end)

class TabStop(TextObject):
    """
    This is the most important TextObject. A TabStop is were the cursor
    comes to rest when the user taps through the Snippet.
    """
    def __init__(self, parent, token, start = None, end = None):
        if start is not None:
            self._no = token
            TextObject.__init__(self, parent, start, end)
        else:
            TextObject.__init__(self, parent, token)
            self._no = token.no

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

    def __init__(self, parent, indent, initial_text, start = None, end = None, last_re = None, globals = None):
        if start is None:
            start = Position(0,0)
        if end is None:
            end = Position(0,0)

        self.locals = {"match" : last_re}
        self.globals = globals

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
                ts = TabStop(self, 0, start, end)
                self._add_tabstop(0,ts)

                self.update()

    def __repr__(self):
        return "SnippetInstance(%s -> %s)" % (self._start, self._end)

    def has_tabs(self):
        return len(self._tabstops)
    has_tabs = property(has_tabs)

    def _get_tabstop(self, requester, no):
        # SnippetInstances are completely self contained, therefore, we do not
        # need to ask our parent for Tabstops
        p = self._parent
        self._parent = None
        rv = TextObject._get_tabstop(self, requester, no)
        self._parent = p

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
