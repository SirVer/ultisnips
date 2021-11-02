#!/usr/bin/env python3
# encoding: utf-8

"""Base classes for all text objects."""

from UltiSnips import vim_helper
from UltiSnips.position import Position


def _replace_text(buf, start, end, text):
    """Copy the given text to the current buffer, overwriting the span 'start'
    to 'end'."""
    lines = text.split("\n")

    new_end = start.get_text_end(lines)

    before = buf[start.line][: start.col]
    after = buf[end.line][end.col :]

    new_lines = []
    if len(lines):
        new_lines.append(before + lines[0])
        new_lines.extend(lines[1:])
        new_lines[-1] += after
    buf[start.line : end.line + 1] = new_lines

    return new_end


# These classes use their subclasses a lot and we really do not want to expose
# their functions more globally.
# pylint: disable=protected-access


class TextObject:

    """Represents any object in the text that has a span in any ways."""

    def __init__(
        self,
        parent,
        token_or_start,
        end=None,
        initial_text="",
        tiebreaker=None,
    ):
        self._parent = parent

        if end is not None:  # Took 4 arguments
            self._start = token_or_start
            self._end = end
            self._initial_text = initial_text
        else:  # Initialize from token
            self._start = token_or_start.start
            self._end = token_or_start.end
            self._initial_text = token_or_start.initial_text
            if tiebreaker is None :
                tiebreaker = token_or_start.tiebreaker
        self._tiebreaker = tiebreaker or len(parent._children) if parent is not None else 0
        if parent is not None:
            parent._add_child(self)

    def _move(self, pivot, diff):
        """Move this object by 'diff' while 'pivot' is the point of change."""
        self._start.move(pivot, diff)
        self._end.move(pivot, diff)

    def __lt__(self, other):
        return (self._start, self._tiebreaker) < (other._start, other._tiebreaker)

    def __le__(self, other):
        return (self._start, self._tiebreaker) <= (other._start, other._tiebreaker)

    def __repr__(self):
        ct = ""
        try:
            ct = self.current_text
        except IndexError:
            ct = "<err>"

        return "%s(%r->%r,%r)" % (self.__class__.__name__, self._start, self._end, ct)

    @property
    def current_text(self):
        """The current text of this object."""
        if self._start.line == self._end.line:
            return vim_helper.buf[self._start.line][self._start.col : self._end.col]
        else:
            lines = [vim_helper.buf[self._start.line][self._start.col :]]
            lines.extend(vim_helper.buf[self._start.line + 1 : self._end.line])
            lines.append(vim_helper.buf[self._end.line][: self._end.col])
            return "\n".join(lines)

    @property
    def start(self):
        """The start position."""
        return self._start

    @property
    def end(self):
        """The end position."""
        return self._end

    def overwrite_with_initial_text(self, buf):
        self.overwrite(buf, self._initial_text)

    def overwrite(self, buf, gtext):
        """Overwrite the text of this object in the Vim Buffer and update its
        length information.

        If 'gtext' is None use the initial text of this object.

        """
        # We explicitly do not want to move our children around here as we
        # either have non or we are replacing text initially which means we do
        # not want to mess with their positions
        if self.current_text == gtext:
            return
        old_end = self._end
        self._end = _replace_text(buf, self._start, self._end, gtext)
        if self._parent:
            self._parent._child_has_moved(
                self._parent._children.index(self),
                old_end,
                self._end - old_end,
            )

    def _update(self, todo, buf):
        """Update this object inside 'buf' which is a list of lines.

        Return False if you need to be called again for this edit cycle.
        Otherwise return True.

        """
        raise NotImplementedError("Must be implemented by subclasses.")

    def _sort_children_rec(self):
        """
        Sorte the children once and for all.
        To be reimplemented in sub-class that may be a parent.
        """
        pass


class EditableTextObject(TextObject):

    """This base class represents any object in the text that can be changed by
    the user."""

    def __init__(self, *args, **kwargs):
        self._children = []
        self._is_sorted = False
        self._tabstops = {}
        TextObject.__init__(self, *args, **kwargs)

    ##############
    # Properties #
    ##############
    @property
    def children(self):
        """List of all children."""
        return self._children

    @property
    def _editable_children(self):
        """List of all children that are EditableTextObjects."""
        return [
            child for child in self._children if isinstance(child, EditableTextObject)
        ]

    ####################
    # Public Functions #
    ####################
    def find_parent_for_new_to(self, pos):
        """Figure out the parent object for something at 'pos'."""
        for children in self._editable_children:
            if children._start <= pos < children._end:
                return children.find_parent_for_new_to(pos)
            if children._start == pos and pos == children._end:
                return children.find_parent_for_new_to(pos)
        return self

    ###############################
    # Private/Protected functions #
    ###############################
    def _do_edit(self, cmd, ctab=None):
        """
        Apply the edit 'cmd' to this object.
        Killed objects are the one manually altered by the user,
        they should be removed from the tracked objects since we don't
        want to erase what the user type.
        """
        ctype, line, col, text = cmd
        assert ("\n" not in text) or (text == "\n")
        start_pos, end_pos = Position._create_edit_start_end_pos(line, col, text)

        to_kill = set()
        new_cmds = []
        for child in self._children:
            if ctype == "I":  # Insertion
                if child._start < start_pos < Position(
                    child._end.line, child._end.col
                ) and isinstance(child, NoneditableTextObject):
                    to_kill.add(child)
                    new_cmds.append(cmd)
                    break
                elif (child._start <= start_pos <= child._end) and isinstance(
                    child, EditableTextObject
                ):
                    if start_pos == child.end and not child.children:
                        try:
                            if ctab.number != child.number:
                                continue
                        except AttributeError: # ( If the child is not a tabstop )
                            pass
                    child._do_edit(cmd, ctab)
                    return
            else:  # Deletion
                if (child._start <= start_pos < child._end) and (
                    child._start < end_pos <= child._end
                ):
                    # this edit command is completely for the child
                    if isinstance(child, NoneditableTextObject):
                        to_kill.add(child)
                        new_cmds.append(cmd)
                        break
                    else:
                        child._do_edit(cmd, ctab)
                        return
                elif (
                    start_pos < child._start < end_pos  and child._end <= end_pos
                ) or (start_pos <= child._start and child._end < end_pos):
                    # Case: this deletion removes the child
                    to_kill.add(child)
                    new_cmds.append(cmd)
                    break
                # Partially for us and partially for the child, break the command in two exclusive one and recurse.
                elif start_pos < child._start and (child._start < end_pos <= child._end):
                    # Case: partially for us, partially for the child
                    my_text = text[: (child._start - start_pos).col]
                    c_text = text[(child._start - start_pos).col :]
                    new_cmds.append((ctype, line, col, my_text))
                    new_cmds.append((ctype, line, col, c_text))
                    break
                elif end_pos >= child._end and (child._start <= start_pos < child._end):
                    # Case: partially for the child, partially for us
                    c_text = text[(child._end - start_pos).col :]
                    my_text = text[: (child._end - start_pos).col]
                    new_cmds.append((ctype, line, col, c_text))
                    new_cmds.append((ctype, line, col, my_text))
                    break

        for child in to_kill:
            self._del_child(child)
        if len(new_cmds):
            for new_cmd in new_cmds:
                self._do_edit(new_cmd)
            return

        if ctype == "D" and self._start == self._end:
            # Makes no sense to delete in empty textobject
            return
          
        # We have to handle this ourselves
        pivot, delta = Position._create_pivot_delta_for_edit_cmd(cmd)
        idx = -1
        for cidx, child in enumerate(self._children):
            if child._start < pivot <= child._end:
                idx = cidx
        self._child_has_moved(idx, pivot, delta)

    def _move(self, pivot, diff):
        TextObject._move(self, pivot, diff)

        for child in self._children:
            child._move(pivot, diff)

    def _child_has_moved(self, idx, pivot, diff):
        """Called when a the child with 'idx' has moved behind 'pivot' by
        'diff'."""
        self._end.move(pivot, diff)

        for child in self._children[idx + 1:]:
            child._move(pivot, diff)

        if self._parent:
            self._parent._child_has_moved(
                self._parent._children.index(self), pivot, diff
            )

    def _get_next_tab(self, number):
        """Returns the next tabstop after 'number'."""
        if not len(self._tabstops.keys()):
            return
        tno_max = max(self._tabstops.keys())

        possible_sol = []
        i = number + 1
        while i <= tno_max:
            if i in self._tabstops:
                possible_sol.append((i, self._tabstops[i]))
                break
            i += 1

        child = [c._get_next_tab(number) for c in self._editable_children]
        child = [c for c in child if c]

        possible_sol += child

        if not len(possible_sol):
            return None

        return min(possible_sol)

    def _get_prev_tab(self, number):
        """Returns the previous tabstop before 'number'."""
        if not len(self._tabstops.keys()):
            return
        tno_min = min(self._tabstops.keys())

        possible_sol = []
        i = number - 1
        while i >= tno_min and i > 0:
            if i in self._tabstops:
                possible_sol.append((i, self._tabstops[i]))
                break
            i -= 1

        child = [c._get_prev_tab(number) for c in self._editable_children]
        child = [c for c in child if c]

        possible_sol += child

        if not len(possible_sol):
            return None

        return max(possible_sol)

    def _get_tabstop(self, requester, number):
        """Returns the tabstop 'number'.

        'requester' is the class that is interested in this.

        """
        if number in self._tabstops:
            return self._tabstops[number]
        for child in self._editable_children:
            if child is requester:
                continue
            rv = child._get_tabstop(self, number)
            if rv is not None:
                return rv
        if self._parent and requester is not self._parent:
            return self._parent._get_tabstop(self, number)

    def _update(self, todo, buf):
        return not any(
            (child in todo)
            for child in self._children
        )

    def _add_child(self, child):
        """Add 'child' as a new child of this text object."""
        self._children.append(child)
        # If the child is added on-fly, we need to maintain the order
        # but if it's part of the optimization, no need bothering
        # because it will be done once and for all from SnippetDefinition.launch()
        if self._is_sorted :  
            child._sort_children_rec()
            self._children.sort()


    def _del_child(self, child):
        """Delete this 'child'."""
        child._parent = None
        self._children.remove(child)

        # If this is a tabstop, delete it. Might have been deleted already if
        # it was nested.
        try:
            del self._tabstops[child.number]
        except (AttributeError, KeyError):
            pass
          
    def _sort_children_rec(self):
        for child in self._children :
            child._sort_children_rec()
        self._children.sort()
        self._is_sorted = True


class NoneditableTextObject(TextObject):

    """All passive text objects that the user can't edit by hand."""

    def _update(self, todo, buf):
        return True
