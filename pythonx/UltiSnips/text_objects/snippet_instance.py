#!/usr/bin/env python3

"""A Snippet instance is an instance of a Snippet Definition.

That is, when the user expands a snippet, a SnippetInstance is created
to keep track of the corresponding TextObjects. The Snippet itself is
also a TextObject.

"""

from collections import namedtuple

from UltiSnips import vim_helper
from UltiSnips.error import PebkacError
from UltiSnips.position import JumpDirection, Position
from UltiSnips.text_objects.base import EditableTextObject, NoneditableTextObject
from UltiSnips.text_objects.tabstop import TabStop

_VisualContentSnapshot = namedtuple("_VisualContentSnapshot", ["mode", "text"])


class SnippetInstance(EditableTextObject):
    """See module docstring."""

    def __init__(
        self,
        snippet,
        parent,
        initial_text,
        start,
        end,
        visual_content,
        last_re,
        globals,
        context,
        _compiled_globals=None,
    ):
        if start is None:
            start = Position(0, 0)
        if end is None:
            end = Position(0, 0)
        self.snippet = snippet
        self._cts = 0

        self.context = context
        self.locals = {"match": last_re, "context": context}
        self.globals = globals
        self._compiled_globals = _compiled_globals
        # Snapshot mode + text right at launch. The live preserver gets
        # reset() immediately after launch returns, so any later read
        # (e.g. inside `post_jump` / `post_finish`) needs a frozen view.
        if visual_content is None:
            self.visual_content = _VisualContentSnapshot("", "")
        else:
            self.visual_content = _VisualContentSnapshot(
                visual_content.mode, visual_content.text
            )
        self.current_placeholder = None

        super().__init__(parent, start, end, initial_text)

    def replace_initial_text(self, buf):
        """Puts the initial text of all text elements into Vim."""

        def _place_initial_text(obj):
            """recurses on the children to do the work."""
            obj.overwrite_with_initial_text(buf)
            if isinstance(obj, EditableTextObject):
                for child in obj._children:
                    _place_initial_text(child)

        _place_initial_text(self)

    def replay_user_edits(self, cmds, ctab=None):
        """Replay the edits the user has done to keep endings of our Text
        objects in sync with reality."""
        for cmd in cmds:
            self._do_edit(cmd, ctab)

    def update_textobjects(self, buf, ctab=None):
        """Update the text objects that should change automagically after the
        users edits have been replayed.

        This might also move the Cursor

        """
        done = set()
        not_done = set()

        def _contains_ctab(obj):
            """True if obj is ctab or one of its ancestors."""
            if ctab is None:
                return False
            cur = ctab
            while cur is not None:
                if cur is obj:
                    return True
                cur = cur._parent
            return False

        def _find_recursive(obj):
            """Finds all text objects and puts them into 'not_done'."""
            cursorInsideLowest = None
            if isinstance(obj, EditableTextObject):
                if obj.start <= vim_helper.buf.cursor <= obj.end and not (
                    isinstance(obj, TabStop) and obj.number == 0
                ):
                    cursorInsideLowest = obj
                # Two siblings can both contain the cursor at a zero-width
                # seam — e.g. `$1$2` immediately after expansion, or `$1$1$2`
                # once `$1` has accumulated content and its mirror sits at
                # the same column as the next tabstop. The last sibling
                # would win the naive `or cursorInsideLowest` chain, but the
                # currently-selected tabstop is where the user is editing,
                # so prefer that branch. Without this, a mirror update
                # inside the wrong sibling drags the cursor with it and
                # subsequent typing falls outside any tabstop. See #1359.
                preferred = None
                fallback = cursorInsideLowest
                for child in obj._children:
                    child_match = _find_recursive(child)
                    if child_match is None:
                        continue
                    if _contains_ctab(child):
                        preferred = child_match
                    else:
                        fallback = child_match
                cursorInsideLowest = preferred or fallback
            not_done.add(obj)
            return cursorInsideLowest

        cursorInsideLowest = _find_recursive(self)
        if cursorInsideLowest is not None:
            vc = _VimCursor(cursorInsideLowest)
        counter = 10
        while (done != not_done) and counter:
            # Order matters for python locals!
            for obj in sorted(not_done - done):
                if obj._update(done, buf):
                    done.add(obj)
            counter -= 1
        if not counter:
            raise PebkacError(
                "The snippets content did not converge: Check for Cyclic "
                "dependencies or random strings in your snippet. You can use "
                "'if not snip.c' to make sure to only expand random output "
                "once."
            )
        if cursorInsideLowest is not None:
            vc.to_vim()
            cursorInsideLowest._del_child(vc)

    def select_next_tab(self, jump_direction: JumpDirection):
        """Selects the next tabstop in the direction of 'jump_direction'."""
        if self._cts is None:
            return

        if jump_direction == JumpDirection.BACKWARD:
            current_tabstop_backup = self._cts

            res = self._get_prev_tab(self._cts)
            if res is None:
                self._cts = current_tabstop_backup
                return self._tabstops.get(self._cts, None)
            self._cts, ts = res
            return ts
        if jump_direction == JumpDirection.FORWARD:
            res = self._get_next_tab(self._cts)
            if res is None:
                self._cts = None

                ts = self._get_tabstop(self, 0)
                if ts:
                    return ts

                # TabStop 0 was deleted. It was probably killed through some
                # edit action. Recreate it at the end of us.
                start = Position(self.end.line, self.end.col)
                end = Position(self.end.line, self.end.col)
                return TabStop(self, 0, start, end)
            self._cts, ts = res
            return ts
        raise AssertionError(f"Unknown JumpDirection: {jump_direction!r}")

    def has_next_tab(self, jump_direction: JumpDirection):
        if jump_direction == JumpDirection.BACKWARD:
            return self._get_prev_tab(self._cts) is not None
        # There is always a next tabstop if we jump forward, since the snippet
        # instance is deleted once we reach tabstop 0.
        return True

    def _get_tabstop(self, requester, no):
        # SnippetInstances are completely self contained, therefore, we do not
        # need to ask our parent for Tabstops
        cached_parent = self._parent
        self._parent = None
        rv = EditableTextObject._get_tabstop(self, requester, no)
        self._parent = cached_parent
        return rv

    def get_tabstops(self):
        return self._tabstops


class _VimCursor(NoneditableTextObject):
    """Helper class to keep track of the Vim Cursor when text objects expand
    and move."""

    def __init__(self, parent):
        super().__init__(
            parent,
            vim_helper.buf.cursor,
            vim_helper.buf.cursor,
            tiebreaker=Position(-1, -1),
        )

    def to_vim(self):
        """Moves the cursor in the Vim to our position."""
        assert self._start == self._end
        vim_helper.buf.cursor = self._start
