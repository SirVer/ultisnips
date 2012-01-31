#!/usr/bin/env python
# encoding: utf-8

import vim

import UltiSnips._vim as _vim
from UltiSnips.geometry import Position

__all__ = ["TextObject", "EditableTextObject", "NoneditableTextObject"]

class TextObject(object):
    """
    This base class represents any object in the text
    that has a span in any ways
    """
    def __init__(self, parent, token, end = None, initial_text = "", tiebreaker = None):
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
        self._tiebreaker = tiebreaker or Position(self._start.line, self._end.line)

        if parent is not None:
            parent._add_child(self)

    def overwrite(self, gtext = None):
        """
        Overwrite the text of this object in the Vim Buffer and update its
        length information
        """
        # We explicitly do not want to move our childs around here as we
        # either have non or we are replacing text initially which means we do
        # not want to mess with their positions
        if self.current_text == gtext: return
        old_end = self._end
        self._end = _vim.text_to_vim(
                self._start, self._end, gtext or self._initial_text)
        if self._parent:
            self._parent._child_has_moved(
                self._parent._childs.index(self), min(old_end, self._end),
                self._end.diff(old_end)
            )

    def __lt__(self, other):
        me = (self._start.line, self._start.col,
                self._tiebreaker.line, self._tiebreaker.col)
        o = (other._start.line, other._start.col,
                other._tiebreaker.line, other._tiebreaker.col)
        return me < o
    def __le__(self, other):
        me = (self._start.line, self._start.col,
                self._tiebreaker.line, self._tiebreaker.col)
        o = (other._start.line, other._start.col,
                other._tiebreaker.line, other._tiebreaker.col)
        return me <= o

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
        if self._start.line == self._end.line:
            return _vim.buf[self._start.line][self._start.col:self._end.col]
        else:
            lines = [_vim.buf[self._start.line][self._start.col:]]
            lines.extend(_vim.buf[self._start.line+1:self._end.line])
            lines.append(_vim.buf[self._end.line][:self._end.col])
            return '\n'.join(lines)

    def start(self):
        return self._start
    start = property(start)

    def end(self):
        return self._end
    end = property(end)

    ####################
    # Public functions #
    ####################
    def _move(self, pivot, diff):
        self._start.move(pivot, diff)
        self._end.move(pivot, diff)

class EditableTextObject(TextObject):
    """
    This base class represents any object in the text
    that can be changed by the user
    """
    def __init__(self, *args, **kwargs):
        TextObject.__init__(self, *args, **kwargs)

        self._childs = []
        self._tabstops = {}

    ##############
    # Properties #
    ##############
    @property
    def _editable_childs(self):
        return [ c for c in self._childs if isinstance(c, EditableTextObject) ]

    ####################
    # Public Functions #
    ####################
    def find_parent_for_new_to(self, pos):
        for c in self._editable_childs:
            if (c._start <= pos < c._end):
                return c.find_parent_for_new_to(pos)
        return self

    ###############################
    # Private/Protected functions #
    ###############################
    def _do_edit(self, cmd):
        ctype, line, col, text = cmd
        assert( ('\n' not in text) or (text == "\n"))
        pos = Position(line, col)

        to_kill = set()
        new_cmds = []
        for c in self._childs:
            if ctype == "I": # Insertion
                if c._start < pos < Position(c._end.line, c._end.col) and isinstance(c, NoneditableTextObject):
                    to_kill.add(c)
                    new_cmds.append(cmd)
                    break
                elif (c._start <= pos <= c._end) and isinstance(c, EditableTextObject):
                    c._do_edit(cmd)
                    return
            else: # Deletion
                delend = pos + Position(0, len(text)) if text != "\n" \
                        else Position(line + 1, 0)
                if (c._start <= pos < c._end) and (c._start < delend <= c._end):
                    # this edit command is completely for the child
                    if isinstance(c, NoneditableTextObject):
                        to_kill.add(c)
                        new_cmds.append(cmd)
                        break
                    else:
                        c._do_edit(cmd)
                        return
                elif (pos < c._start and c._end <= delend) or (pos <= c._start and c._end < delend):
                    # Case: this deletion removes the child
                    to_kill.add(c)
                    new_cmds.append(cmd)
                    break
                elif (pos < c._start and (c._start < delend <= c._end)):
                    # Case: partially for us, partially for the child
                    my_text = text[:(c._start-pos).col]
                    c_text = text[(c._start-pos).col:]
                    new_cmds.append((ctype, line, col, my_text))
                    new_cmds.append((ctype, line, col, c_text))
                    break
                elif (delend >= c._end and (c._start <= pos < c._end)):
                    # Case: partially for us, partially for the child
                    c_text = text[(c._end-pos).col:]
                    my_text = text[:(c._end-pos).col]
                    new_cmds.append((ctype, line, col, c_text))
                    new_cmds.append((ctype, line, col, my_text))
                    break

        for c in to_kill:
            self._del_child(c)
        if len(new_cmds):
            for c in new_cmds:
                self._do_edit(c)
            return

        # We have to handle this ourselves
        delta = Position(1, 0) if text == "\n" else Position(0, len(text))
        if ctype == "D":
            if self._start == self._end: # Makes no sense to delete in empty textobject
                return
            delta.line *= -1
            delta.col *= -1
        pivot = Position(line, col)
        idx = -1
        for cidx, c in enumerate(self._childs):
            if c._start < pivot <= c._end:
                idx = cidx
        self._child_has_moved(idx, pivot, delta)

    def _move(self, pivot, diff):
        TextObject._move(self, pivot, diff)

        for c in self._childs:
            c._move(pivot, diff)

    def _child_has_moved(self, idx, pivot, diff):
        self._end.move(pivot, diff)

        for c in self._childs[idx+1:]:
            c._move(pivot, diff)

        if self._parent:
            self._parent._child_has_moved(
                self._parent._childs.index(self), pivot, diff
            )

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

        c = [ c._get_next_tab(no) for c in self._editable_childs ]
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

        c = [ c._get_prev_tab(no) for c in self._editable_childs ]
        c = filter(lambda i: i, c)

        possible_sol += c

        if not len(possible_sol):
            return None

        return max(possible_sol)

    def _get_tabstop(self, requester, no):
        if no in self._tabstops:
            return self._tabstops[no]
        for c in self._editable_childs:
            if c is requester:
                continue

            rv = c._get_tabstop(self, no)
            if rv is not None:
                return rv
        if self._parent and requester is not self._parent:
            return self._parent._get_tabstop(self, no)

    def _update(self, done, not_done):
        """
        Update this object inside the Vim Buffer.

        Return False if you want to be called again
        for this edit cycle. Otherwise return True.
        """
        if all((c in done) for c in self._childs):
            assert(self not in done)

            done.add(self)
        return True

    def _add_child(self,c):
        self._childs.append(c)
        self._childs.sort()

    def _del_child(self,c):
        c._parent = None
        self._childs.remove(c)

        # If this is a tabstop, delete it
        try:
            del self._tabstops[c.no]
        except AttributeError:
            pass

class NoneditableTextObject(TextObject):
    """
    All passive text objects that the user can't edit by hand
    """

    def _update(self, done, not_done):
        return True

