#!/usr/bin/env python
# encoding: utf-8

import vim

from ..debug import debug, echo_to_hierarchy

from UltiSnips.Buffer import TextBuffer
from UltiSnips.Compatibility import as_unicode
from UltiSnips.Geometry import Span, Position

__all__ = ["TextObject", "NoneditableTextObject"]

class TextObject(object):
    """
    This base class represents any object in the text
    that has a span in any ways
    """
    def __init__(self, parent, token, end = None, initial_text = ""):
        self._parent = parent

        ct = None
        if end is not None: # Took 4 arguments
            self._start = token
            self._end = end
            self._initial_text = initial_text
        else: # Initialize from token
            self._start = token.start
            self._end = token.end
            self._initial_text = token.initial_text

        self._childs = []
        self._tabstops = {}

        if parent is not None:
            parent._add_child(self)

        self._cts = 0
        self._is_killed = False # TODO: not often needed

    def overwrite(self, gtext = None):
        """
        Overwrite the text of this object in the Vim Buffer and update its
        length information
        """
        old_end = self._end
        self._end = TextBuffer(gtext or self._initial_text).to_vim(self._start, self._end)

        # TODO: child_end_moved3 is a stupid name for this function
        self.child_end_moved3(min(old_end, self._end), self._end.gsub(old_end))

    def __lt__(self, other):
        return self._start < other._start
    def __le__(self, other):
        return self._start <= other._start

    def __repr__(self):
        ct = ""
        try:
            ct = self.current_text
        except IndexError:
            ct = "<err>"

        return "%s(%r->%r,%r)" % (self.__class__.__name__,
                self._start, self._end, ct)

    ##############
    # PROPERTIES #
    ##############
    @property
    def current_text(self):
        _span = self.span
        buf = vim.current.buffer

        if _span.start.line == _span.end.line:
            return as_unicode(buf[_span.start.line])[_span.start.col:_span.end.col]
        else:
            lines = []
            lines.append(as_unicode(buf[_span.start.line])[_span.start.col:])
            lines.extend(map(as_unicode, buf[_span.start.line+1:_span.end.line]))
            lines.append(as_unicode(buf[_span.end.line])[:_span.end.col])
            return as_unicode('\n').join(lines)

    @property
    def current_tabstop(self):
        if self._cts is None:
            return None
        return self._tabstops[self._cts]

    def span(self):
        return Span(self._start, self._end)
    span = property(span)

    def start(self):
        return self._start
    start = property(start)

    def end(self):
        return self._end
    end = property(end)

    ####################
    # Public functions #
    ####################
    def _find_parent_for_new_to(self, pos):
        assert(pos in self.span)

        for c in self._childs: # TODO: code duplication!
            if isinstance(c, NoneditableTextObject): # TODO: make this nicer
                continue
            if (c._start <= pos <= c._end):
                return c._find_parent_for_new_to(pos)
        return self

    def child_end_moved3(self, pivot, diff):
        if not (self._parent):
            return

        self._parent._end.move(pivot, diff)
        def _move_all(o):
            o._start.move(pivot, diff)
            o._end.move(pivot, diff)

            for oc in o._childs:
                _move_all(oc)

        for c in self._parent._childs[self._parent._childs.index(self)+1:]:
            _move_all(c)

        self._parent.child_end_moved3(pivot, diff)

    def _do_edit(self, cmd):
        debug("cmd: %r, self: %r" % (cmd, self))
        ctype, line, col, char = cmd
        assert( ('\n' not in char) or (char == "\n"))
        pos = Position(line, col)

        to_kill = set()
        new_cmds = []
        for c in self._childs:
            start = c._start
            end = c._end

            debug("consider: c: %r" % (c))
            if ctype == "D":
                if char == "\n":
                    delend = Position(line + 1, 0) # TODO: is this even needed?
                else:
                    delend = pos + Position(0, len(char))
                # TODO: char is no longer true -> Text
                # Case: this deletion removes the child
                # Case: this edit command is completely for the child
                if (start <= pos < end) and (start < delend <= end):
                    debug("Case 2")
                    if isinstance(c, NoneditableTextObject): # Erasing inside NonTabstop -> Kill element
                        to_kill.add(c)
                        continue
                    c._do_edit(cmd)
                    return
                elif (pos < start and end <= delend) or (pos <= start and end < delend):
                    debug("Case 1")
                    to_kill.add(c)
                # Case: partially for us, partially for the child
                elif (pos < start and (start < delend <= end)):
                    debug("Case 3")
                    my_text = char[:(start-pos).col]
                    c_text = char[(start-pos).col:]
                    debug("my_text: %r, c_text: %r" % (my_text, c_text))
                    new_cmds.append((ctype, line, col, my_text))
                    new_cmds.append((ctype, line, col, c_text))
                    break
                elif (delend >= end and (start <= pos < end)):
                    debug("Case 3")
                    c_text = char[(end-pos).col:]
                    my_text = char[:(end-pos).col]
                    debug("my_text: %r, c_text: %r" % (my_text, c_text))
                    new_cmds.append((ctype, line, col, c_text))
                    new_cmds.append((ctype, line, col, my_text))
                    break
            elif ctype == "I": # Else would be okay as well
                if isinstance(c, NoneditableTextObject): # TODO: make this nicer
                    continue
                if (start <= pos <= end):
                    c._do_edit(cmd)
                    return

        for c in to_kill:
            self._del_child(c)
        if len(new_cmds):
            for c in new_cmds:
                self._do_edit(c)
            return


        # We have to handle this ourselves
        if ctype == "D": # TODO: code duplication
            assert(self._start != self._end) # Makes no sense to delete in empty textobject

            if char == "\n":
                delta = Position(-1, 0) # TODO: this feels somehow incorrect:
            else:
                delta = Position(0, -len(char))
        else:
            if char == "\n":
                delta = Position(1, 0) # TODO: this feels somehow incorrect
            else:
                delta = Position(0, len(char))
        pivot = Position(line, col)
        # TODO: this should somehow be part of child_end_moved3
        for c in self._childs:
            c._start.move(pivot, delta)
            c._end.move(pivot, delta)
        self._end.move(pivot, delta)
        self.child_end_moved3(pivot, delta)

    def edited(self, cmds): # TODO: Only in SnippetInstance
        # Replay User Edits to update end of our current texts
        for cmd in cmds:
            self._do_edit(cmd)

    def do_edits(self): # TODO: only in snippets instance, stupid name
        # Do our own edits; keep track of the Cursor
        vc = _VimCursor(self)

        done = set()
        not_done = set()

        def _find_recursive(obj):
            for c in obj._childs:
                _find_recursive(c)
            not_done.add(obj)

        _find_recursive(self)

        counter = 10
        while (done != not_done) and counter:
            for obj in (not_done - done):
                obj._update_if_not_done(done, not_done)
            counter -= 1
        if counter == 0:
            raise RuntimeError("Cyclic dependency in TextElements!")


        vc.update_position()
        self._del_child(vc)


    def _get_next_tab(self, no):
        if not len(self._tabstops.keys()):
            return
        tno_max = max(self._tabstops.keys())

        possible_sol = []
        i = no + 1
        while i <= tno_max:
            if i in self._tabstops:
                possible_sol.append( (i, self._tabstops[i]) )
                break
            i += 1

        c = [ c._get_next_tab(no) for c in self._childs ]
        c = filter(lambda i: i, c)

        possible_sol += c

        if not len(possible_sol):
            return None

        return min(possible_sol)


    def _get_prev_tab(self, no):
        if not len(self._tabstops.keys()):
            return
        tno_min = min(self._tabstops.keys())

        possible_sol = []
        i = no - 1
        while i >= tno_min and i > 0:
            if i in self._tabstops:
                possible_sol.append( (i, self._tabstops[i]) )
                break
            i -= 1

        c = [ c._get_prev_tab(no) for c in self._childs ]
        c = filter(lambda i: i, c)

        possible_sol += c

        if not len(possible_sol):
            return None

        return max(possible_sol)

    ###############################
    # Private/Protected functions #
    ###############################
    def _update(self, done, not_done):
        """
        Return False if you want to be called again
        for this edit cycle. Otherwise return True.
        """
        return True

    def _update_if_not_done(self, done, not_done): # TODO:
        if all((c in done) for c in self._childs):
            assert(self not in done)

            if self._update(done, not_done):
                done.add(self)

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

    def _del_child(self,c):
        c._is_killed = True # TODO: private parts
        self._childs.remove(c)

        # If this is a tabstop, delete it
        try:
            del self._tabstops[c.no]
        except AttributeError:
            pass

    def _add_tabstop(self, ts): # Why is tabstop not doing this in __init__? TODO
        self._tabstops[ts.no] = ts

class NoneditableTextObject(TextObject):
    """
    All passive text objects that the user can't edit by hand
    """
    pass


class _VimCursor(NoneditableTextObject):
    def __init__(self, parent):
        """Helperclass to keep track of the vim Cursor"""
        line, col = vim.current.window.cursor # TODO: some schenanigans like col -> byte?
        s = Position(line-1, col)
        e = Position(line-1, col)
        NoneditableTextObject.__init__(self, parent, s, e)

    def update_position(self):
        assert(self._start == self._end)
        vim.current.window.cursor = (self._start.line + 1, self._start.col)


