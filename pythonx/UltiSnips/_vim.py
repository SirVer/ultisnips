#!/usr/bin/env python
# encoding: utf-8

"""Wrapper functionality around the functions we need from Vim."""

import re

import vim  # pylint:disable=import-error
from vim import error  # pylint:disable=import-error,unused-import

from UltiSnips.compatibility import col2byte, byte2col, \
    as_unicode, as_vimencoding
from UltiSnips.position import Position

from contextlib import contextmanager


class VimBuffer(object):

    """Wrapper around the current Vim buffer."""

    def __getitem__(self, idx):
        if isinstance(idx, slice):  # Py3
            return self.__getslice__(idx.start, idx.stop)
        rv = vim.current.buffer[idx]
        return as_unicode(rv)

    def __getslice__(self, i, j):  # pylint:disable=no-self-use
        rv = vim.current.buffer[i:j]
        return [as_unicode(l) for l in rv]

    def __setitem__(self, idx, text):
        if isinstance(idx, slice):  # Py3
            return self.__setslice__(idx.start, idx.stop, text)
        vim.current.buffer[idx] = as_vimencoding(text)

    def __setslice__(self, i, j, text):  # pylint:disable=no-self-use
        vim.current.buffer[i:j] = [as_vimencoding(l) for l in text]

    def __len__(self):
        return len(vim.current.buffer)

    @property
    def line_till_cursor(self):  # pylint:disable=no-self-use
        """Returns the text before the cursor."""
        _, col = self.cursor
        return as_unicode(vim.current.line)[:col]

    @property
    def number(self):  # pylint:disable=no-self-use
        """The bufnr() of the current buffer."""
        return vim.current.buffer.number

    @property
    def cursor(self):  # pylint:disable=no-self-use
        """The current windows cursor.

        Note that this is 0 based in col and 0 based in line which is
        different from Vim's cursor.

        """
        line, nbyte = vim.current.window.cursor
        col = byte2col(line, nbyte)
        return Position(line - 1, col)

    @cursor.setter
    def cursor(self, pos):  # pylint:disable=no-self-use
        """See getter."""
        nbyte = col2byte(pos.line + 1, pos.col)
        vim.current.window.cursor = pos.line + 1, nbyte
buf = VimBuffer()  # pylint:disable=invalid-name

@contextmanager
def toggle_opt(name, new_value):
    old_value = eval('&' + name)
    command('set {0}={1}'.format(name, new_value))
    try:
        yield
    finally:
        command('set {0}={1}'.format(name, old_value))

@contextmanager
def save_mark(name):
    old_pos = get_mark_pos(name)
    try:
        yield
    finally:
        if _is_pos_zero(old_pos):
            delete_mark(name)
        else:
            set_mark_from_pos(name, old_pos)

def escape(inp):
    """Creates a vim-friendly string from a group of
    dicts, lists and strings."""
    def conv(obj):
        """Convert obj."""
        if isinstance(obj, list):
            rv = as_unicode('[' + ','.join(conv(o) for o in obj) + ']')
        elif isinstance(obj, dict):
            rv = as_unicode('{' + ','.join([
                '%s:%s' % (conv(key), conv(value))
                for key, value in obj.iteritems()]) + '}')
        else:
            rv = as_unicode('"%s"') % as_unicode(obj).replace('"', '\\"')
        return rv
    return conv(inp)


def command(cmd):
    """Wraps vim.command."""
    return as_unicode(vim.command(as_vimencoding(cmd)))


def eval(text):
    """Wraps vim.eval."""
    rv = vim.eval(as_vimencoding(text))
    if not isinstance(rv, (dict, list)):
        return as_unicode(rv)
    return rv


def feedkeys(keys, mode='n'):
    """Wrapper around vim's feedkeys function.

    Mainly for convenience.

    """
    if eval('mode()') == 'n':
        if keys == 'a':
            cursor_pos = get_cursor_pos()
            cursor_pos[2] = int(cursor_pos[2]) + 1
            set_cursor_from_pos(cursor_pos)
        if keys in 'ai':
            keys = 'startinsert'

    if keys == 'startinsert':
        command('startinsert')
    else:
        command(as_unicode(r'call feedkeys("%s", "%s")') % (keys, mode))


def new_scratch_buffer(text):
    """Create a new scratch buffer with the text given."""
    vim.command('botright new')
    vim.command('set ft=')
    vim.command('set buftype=nofile')

    vim.current.buffer[:] = text.splitlines()

    feedkeys(r"\<Esc>")


def virtual_position(line, col):
    """Runs the position through virtcol() and returns the result."""
    nbytes = col2byte(line, col)
    return line, int(eval('virtcol([%d, %d])' % (line, nbytes)))


def select(start, end):
    """Select the span in Select mode."""
    _unmap_select_mode_mapping()

    selection = eval('&selection')

    col = col2byte(start.line + 1, start.col)
    vim.current.window.cursor = start.line + 1, col

    mode = eval('mode()')

    move_cmd = ''
    if mode != 'n':
        move_cmd += r"\<Esc>"

    if start == end:
        # Zero Length Tabstops, use 'i' or 'a'.
        if col == 0 or mode not in 'i' and \
                col < len(buf[start.line]):
            move_cmd += 'i'
        else:
            move_cmd += 'a'
    else:
        # Non zero length, use Visual selection.
        move_cmd += 'v'
        if 'inclusive' in selection:
            if end.col == 0:
                move_cmd += '%iG$' % end.line
            else:
                move_cmd += '%iG%i|' % virtual_position(end.line + 1, end.col)
        elif 'old' in selection:
            move_cmd += '%iG%i|' % virtual_position(end.line + 1, end.col)
        else:
            move_cmd += '%iG%i|' % virtual_position(end.line + 1, end.col + 1)
        move_cmd += 'o%iG%i|o\\<c-g>' % virtual_position(
            start.line + 1, start.col + 1)
    feedkeys(move_cmd)

def set_mark_from_pos(name, pos):
    return _set_pos("'" + name, pos)

def get_mark_pos(name):
    return _get_pos("'" + name)

def set_cursor_from_pos(pos):
    return _set_pos('.', pos)

def get_cursor_pos():
    return _get_pos('.')

def delete_mark(name):
    try:
        return command('delma ' + name)
    except:
        return False

def _set_pos(name, pos):
    return eval("setpos(\"{0}\", {1})".format(name, pos))

def _get_pos(name):
    return eval("getpos(\"{0}\")".format(name))

def _is_pos_zero(pos):
    return ['0'] * 4 == pos or [0] == pos

def _unmap_select_mode_mapping():
    """This function unmaps select mode mappings if so wished by the user.

    Removes select mode mappings that can actually be typed by the user
    (ie, ignores things like <Plug>).

    """
    if int(eval('g:UltiSnipsRemoveSelectModeMappings')):
        ignores = eval('g:UltiSnipsMappingsToIgnore') + ['UltiSnips']

        for option in ('<buffer>', ''):
            # Put all smaps into a var, and then read the var
            command(r"redir => _tmp_smaps | silent smap %s " % option +
                    '| redir END')

            # Check if any mappings where found
            all_maps = list(filter(len, eval(r"_tmp_smaps").splitlines()))
            if len(all_maps) == 1 and all_maps[0][0] not in ' sv':
                # "No maps found". String could be localized. Hopefully
                # it doesn't start with any of these letters in any
                # language
                continue

            # Only keep mappings that should not be ignored
            maps = [m for m in all_maps if
                    not any(i in m for i in ignores) and len(m.strip())]

            for map in maps:
                # The first three chars are the modes, that might be listed.
                # We are not interested in them here.
                trig = map[3:].split()[0] if len(
                    map[3:].split()) != 0 else None

                if trig is None:
                    continue

                # The bar separates commands
                if trig[-1] == '|':
                    trig = trig[:-1] + '<Bar>'

                # Special ones
                if trig[0] == '<':
                    add = False
                    # Only allow these
                    for valid in ['Tab', 'NL', 'CR', 'C-Tab', 'BS']:
                        if trig == '<%s>' % valid:
                            add = True
                    if not add:
                        continue

                # UltiSnips remaps <BS>. Keep this around.
                if trig == '<BS>':
                    continue

                # Actually unmap it
                try:
                    command('silent! sunmap %s %s' % (option, trig))
                except:  # pylint:disable=bare-except
                    # Bug 908139: ignore unmaps that fail because of
                    # unprintable characters. This is not ideal because we
                    # will not be able to unmap lhs with any unprintable
                    # character. If the lhs stats with a printable
                    # character this will leak to the user when he tries to
                    # type this character as a first in a selected tabstop.
                    # This case should be rare enough to not bother us
                    # though.
                    pass
