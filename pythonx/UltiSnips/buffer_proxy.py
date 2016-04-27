# coding=utf8

import vim
import UltiSnips._vim
from UltiSnips.compatibility import as_unicode, as_vimencoding
from UltiSnips.position import Position
from UltiSnips._diff import diff
from UltiSnips import _vim

from contextlib import contextmanager


@contextmanager
def use_proxy_buffer(snippets_stack, vstate):
    """
    Forward all changes made in the buffer to the current snippet stack while
    function call.
    """
    buffer_proxy = VimBufferProxy(snippets_stack, vstate)
    old_buffer = _vim.buf
    try:
        _vim.buf = buffer_proxy
        yield
    finally:
        _vim.buf = old_buffer
    buffer_proxy.validate_buffer()


@contextmanager
def suspend_proxy_edits():
    """
    Prevents changes being applied to the snippet stack while function call.
    """
    if not isinstance(_vim.buf, VimBufferProxy):
        yield
    else:
        try:
            _vim.buf._disable_edits()
            yield
        finally:
            _vim.buf._enable_edits()


class VimBufferProxy(_vim.VimBuffer):
    """
    Proxy object used for tracking changes that made from snippet actions.

    Unfortunately, vim by itself lacks of the API for changing text in
    trackable maner.

    Vim marks offers limited functionality for tracking line additions and
    deletions, but nothing offered for tracking changes withing single line.

    Instance of this class is passed to all snippet actions and behaves as
    internal vim.current.window.buffer.

    All changes that are made by user passed to diff algorithm, and resulting
    diff applied to internal snippet structures to ensure they are in sync with
    actual buffer contents.
    """

    def __init__(self, snippets_stack, vstate):
        """
        Instantiate new object.

        snippets_stack is a slice of currently active snippets.
        """
        self._snippets_stack = snippets_stack
        self._buffer = vim.current.buffer
        self._change_tick = int(vim.eval("b:changedtick"))
        self._forward_edits = True
        self._vstate = vstate

    def is_buffer_changed_outside(self):
        """
        Returns true, if buffer was changed without using proxy object, like
        with vim.command() or through internal vim.current.window.buffer.
        """
        return self._change_tick < int(vim.eval("b:changedtick"))

    def validate_buffer(self):
        """
        Raises exception if buffer is changes beyound proxy object.
        """
        if self.is_buffer_changed_outside():
            raise RuntimeError('buffer was modified using vim.command or ' +
            'vim.current.buffer; that changes are untrackable and leads to ' +
            'errors in snippet expansion; use special variable `snip.buffer` '
            'for buffer modifications.\n\n' +
            'See :help UltiSnips-buffer-proxy for more info.')

    def __setitem__(self, key, value):
        """
        Behaves as vim.current.window.buffer.__setitem__ except it tracks
        changes and applies them to the current snippet stack.
        """
        if isinstance(key, slice):
            value = [as_vimencoding(line) for line in value]
            changes = list(self._get_diff(key.start, key.stop, value))
            self._buffer[key.start:key.stop] = [
                line.strip('\n') for line in value
            ]
        else:
            value = as_vimencoding(value)
            changes = list(self._get_line_diff(key, self._buffer[key], value))
            self._buffer[key] = value

        self._change_tick += 1

        if self._forward_edits:
            for change in changes:
                self._apply_change(change)
            if self._snippets_stack:
                self._vstate.remember_buffer(self._snippets_stack[0])

    def __setslice__(self, i, j, text):
        """
        Same as __setitem__.
        """
        self.__setitem__(slice(i, j), text)

    def __getitem__(self, key):
        """
        Just passing call to the vim.current.window.buffer.__getitem__.
        """
        if isinstance(key, slice):
            return [as_unicode(l) for l in self._buffer[key.start:key.stop]]
        else:
            return as_unicode(self._buffer[key])

    def __getslice__(self, i, j):
        """
        Same as __getitem__.
        """
        return self.__getitem__(slice(i, j))

    def __len__(self):
        """
        Same as len(vim.current.window.buffer).
        """
        return len(self._buffer)

    def append(self, line, line_number=-1):
        """
        Same as vim.current.window.buffer.append(), but with tracking changes.
        """
        if line_number < 0:
            line_number = len(self)
        if not isinstance(line, list):
            line = [line]
        self[line_number:line_number] = [as_vimencoding(l) for l in line]

    def __delitem__(self, key):
        if isinstance(key, slice):
            self.__setitem__(key, [])
        else:
            self.__setitem__(slice(key, key+1), [])

    def _get_diff(self, start, end, new_value):
        """
        Very fast diffing algorithm when changes are across many lines.
        """
        for line_number in range(start, end):
            if line_number < 0:
                line_number = len(self._buffer) + line_number
            yield ('D', line_number, 0, self._buffer[line_number], True)

        if start < 0:
            start = len(self._buffer) + start
        for line_number in range(0, len(new_value)):
            yield ('I', start+line_number, 0, new_value[line_number], True)

    def _get_line_diff(self, line_number, before, after):
        """
        Use precise diffing for tracking changes in single line.
        """
        if before == '':
            for change in self._get_diff(line_number, line_number+1, [after]):
                yield change
        else:
            for change in diff(before, after):
                yield (change[0], line_number, change[2], change[3])

    def _apply_change(self, change):
        """
        Apply changeset to current snippets stack, correctly moving around
        snippet itself or its child.
        """
        if not self._snippets_stack:
            return

        change_type, line_number, column_number, change_text = change[0:4]

        line_before = line_number <= self._snippets_stack[0]._start.line
        column_before = column_number <= self._snippets_stack[0]._start.col
        if line_before and column_before:
            direction = 1
            if change_type == 'D':
                direction = -1

            diff = Position(direction, 0)
            if len(change) != 5:
                diff = Position(0, direction * len(change_text))
            print(change, diff)

            self._snippets_stack[0]._move(
                Position(line_number, column_number),
                diff
            )
        else:
            if line_number > self._snippets_stack[0]._end.line:
                return
            if column_number >= self._snippets_stack[0]._end.col:
                return
            self._snippets_stack[0]._do_edit(change[0:4])

    def _disable_edits(self):
        """
        Temporary disable applying changes to snippets stack. Should be done
        while expanding anonymous snippet in the middle of jump to prevent
        double tracking.
        """
        self._forward_edits = False

    def _enable_edits(self):
        """
        Enables changes forwarding back.
        """
        self._forward_edits = True
