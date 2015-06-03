# coding=utf8

import vim
from UltiSnips.position import Position
from UltiSnips._diff import diff

class VimBufferHelper:
    def __init__(self, snippets_stack):
        self._snippets_stack = snippets_stack
        self._buffer = vim.current.buffer
        self._buffer_copy = self._buffer[:]

    def is_buffer_changed_outside(self):
        if len(self._buffer) != len(self._buffer_copy):
            return True

        for line_number in range(0, len(self._buffer_copy)):
            if self._buffer[line_number] != self._buffer_copy[line_number]:
                return True

        return False

    def validate_buffer(self):
        if self.is_buffer_changed_outside():
            raise RuntimeError('buffer was modified using vim.command or ' +
            'vim.current.buffer; that changes are untrackable and leads to' +
            'errors in snippet expansion; use special variable `buffer` for' +
            'buffer modifications')

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            changes = list(self._get_diff(key.start, key.stop, value))
            self._buffer[key.start:key.stop] = value
            self._buffer_copy[key.start:key.stop] = map(
                lambda line: line.strip('\n'),
                value
            )
        else:
            changes = list(self._get_line_diff(key, self._buffer[key], value))
            self._buffer[key] = value
            self._buffer_copy[key] = value

        for change in changes:
            self._apply_change(change)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self._buffer[key.start:key.stop]
        else:
            return self._buffer[key]

    def __len__(self):
        return len(self._buffer)

    def append(self, line, line_number=-1):
        if line_number < 0:
            line_number = len(self)
        if not isinstance(line, list):
            line = [line]
        self[line_number:line_number] = line

    def __delitem__(self, key):
        if isinstance(key, slice):
            self.__setitem__(key, [])
        else:
            self.__setitem__(slice(key, key+1), [])

    def _get_diff(self, start, end, new_value):
        for line_number in range(start, end):
            yield ('D', line_number, 0, self._buffer[line_number])

        for line_number in range(0, len(new_value)):
            yield ('I', start+line_number, 0, new_value[line_number])

    def _get_line_diff(self, line_number, before, after):
        if before == '':
            for change in self._get_diff(line_number, line_number+1, [after]):
                yield change
        else:
            for change in diff(before, after):
                yield (change[0], line_number, change[2], change[3])

    def _apply_change(self, change):
        if not self._snippets_stack:
            return

        line_number = change[1]
        column_number = change[2]
        line_before = line_number <= self._snippets_stack[0]._start.line
        column_before = column_number <= self._snippets_stack[0]._start.col
        if line_before and column_before:
            direction = 1
            if change[0] == 'D':
                direction = -1

            self._snippets_stack[0]._move(
                Position(line_number, 0),
                Position(direction, 0)
            )
        else:
            self._snippets_stack[0]._do_edit(change)
