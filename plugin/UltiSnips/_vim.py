#!/usr/bin/env python
# encoding: utf-8

"""
Wrapper functionality around the functions we need from Vim
"""
import re

import vim
from vim import error

from UltiSnips.geometry import Position
from UltiSnips.compatibility import col2byte, byte2col, \
        as_unicode, as_vimencoding

class VimBuffer(object):
    def __getitem__(self, idx):
        if isinstance(idx, slice): # Py3
            return self.__getslice__(idx.start, idx.stop)
        rv = vim.current.buffer[idx]
        return as_unicode(rv)
    def __getslice__(self, i, j):
        rv = vim.current.buffer[i:j]
        return [ as_unicode(l) for l in rv ]

    def __setitem__(self, idx, text):
        if isinstance(idx, slice): # Py3
            return self.__setslice__(idx.start, idx.stop, text)
        vim.current.buffer[idx] = as_vimencoding(text)
    def __setslice__(self, i, j, text):
        vim.current.buffer[i:j] = [ as_vimencoding(l) for l in text ]

    def __len__(self):
        return len(vim.current.buffer)

    @property
    def current_line_splitted(self):
        """Returns the text before and after the cursor as a tuple."""
        # Note: we want byte position here
        lineno, col = vim.current.window.cursor

        line = vim.current.line
        before, after = as_unicode(line[:col]), as_unicode(line[col:])
        return before, after

    @property
    def nr(self):
        return int(eval("bufnr('%')"))

    def cursor():
        """
        The current windows cursor. Note that this is 0 based in col and 0
        based in line which is different from Vim's cursor.
        """
        def fget(self):
            line, nbyte = vim.current.window.cursor
            col = byte2col(line, nbyte)
            return Position(line - 1, col)
        def fset(self, pos):
            nbyte = col2byte(pos.line + 1, pos.col)
            vim.current.window.cursor = pos.line + 1, nbyte
        return locals()
    cursor = property(**cursor())
buf = VimBuffer()

def text_to_vim(start, end, text):
    lines = text.split('\n')

    new_end = _calc_end(lines, start)

    before = buf[start.line][:start.col]
    after = buf[end.line][end.col:]

    new_lines = []
    if len(lines):
        new_lines.append(before + lines[0])
        new_lines.extend(lines[1:])
        new_lines[-1] += after
    buf[start.line:end.line + 1] = new_lines

    # Open any folds this might have created
    buf.cursor = start
    vim.command("normal! zv")

    return new_end

def escape(inp):
    """ Creates a vim-friendly string from a group of
    dicts, lists and strings.
    """
    def conv(obj):
        if isinstance(obj, list):
            rv = as_unicode('[' + ','.join(conv(o) for o in obj) + ']')
        elif isinstance(obj, dict):
            rv = as_unicode('{' + ','.join([
                "%s:%s" % (conv(key), conv(value))
                for key, value in obj.iteritems()]) + '}')
        else:
            rv = as_unicode('"%s"') % as_unicode(obj).replace('"', '\\"')
        return rv
    return conv(inp)

def command(s):
    return as_unicode(vim.command(as_vimencoding(s)))

def eval(s):
    rv = vim.eval(as_vimencoding(s))
    if not isinstance(rv, (dict, list)):
        return as_unicode(rv)
    return rv

def feedkeys(s, mode='n'):
    """Wrapper around vim's feedkeys function. Mainly for convenience."""
    command(as_unicode(r'call feedkeys("%s", "%s")') % (s, mode))

def new_scratch_buffer(text):
    """Create a new scratch buffer with the text given"""
    command("botright new")
    command("set ft=text")
    command("set buftype=nofile")

    vim.buffers[-1][:] = text.splitlines()

    feedkeys(r"\<Esc>")

def select(start, end):
    """Select the span in Select mode"""

    _unmap_select_mode_mapping()

    delta = end - start
    lineno, col = start.line, start.col

    col = col2byte(lineno + 1, col)
    vim.current.window.cursor = lineno + 1, col

    move_cmd = ""
    if eval("mode()") != 'n':
        move_cmd += r"\<Esc>"

    # Case 1: Zero Length Tabstops
    if delta.line == delta.col == 0:
        if col == 0 or eval("mode()") not in 'i' and \
                col < len(buf[lineno]):
            move_cmd += "i"
        else:
            move_cmd += "a"
    else:
        # Case 2a: Non zero length
        # If a tabstop immediately starts with a newline, the selection
        # must start after the last character in the current line. But if
        # we are in insert mode and <Esc> out of it, we cannot go past the
        # last character with move_one_right and therefore cannot
        # visual-select this newline. We have to hack around this by adding
        # an extra space which we can select.  Note that this problem could
        # be circumvent by selecting the tab backwards (that is starting
        # at the end); one would not need to modify the line for this. This creates other
        # trouble though
        if col >= len(buf[lineno]):
            buf[lineno] += " "

        if delta.line:
            move_lines = "%ij" % delta.line
        else:
            move_lines = ""
        # Depending on the current mode and position, we
        # might need to move escape out of the mode and this
        # will move our cursor one left
        if col != 0 and eval("mode()") == 'i':
            move_one_right = "l"
        else:
            move_one_right = ""

        # After moving to the correct line, we go back to column 0
        # and select right from there. Note that the we have to select
        # one column less since Vim's visual selection is including the
        # ending while Python slicing is excluding the ending.
        inclusive = "inclusive" in eval("&selection")
        if end.col == 0:
            # Selecting should end at beginning of line -> Select the
            # previous line till its end
            do_select = "k$"
            if not inclusive:
                do_select += "j0"
        elif end.col > 1:
            do_select = "0%il" % (end.col-1 if inclusive else end.col)
        else:
            do_select = "0" if inclusive else "0l"

        move_cmd += _LangMapTranslator().translate(
            r"%sv%s%s\<c-g>" % (move_one_right, move_lines, do_select)
        )

    feedkeys(move_cmd)

# Helper functions  {{{
def _calc_end(lines, start):
    if len(lines) == 1:
        new_end = start + Position(0,len(lines[0]))
    else:
        new_end = Position(start.line + len(lines)-1, len(lines[-1]))
    return new_end

def _unmap_select_mode_mapping():
    """This function unmaps select mode mappings if so wished by the user.
    Removes select mode mappings that can actually be typed by the user
    (ie, ignores things like <Plug>).
    """
    if int(eval("g:UltiSnipsRemoveSelectModeMappings")):
        ignores = eval("g:UltiSnipsMappingsToIgnore") + ['UltiSnips']

        for option in ("<buffer>", ""):
            # Put all smaps into a var, and then read the var
            command(r"redir => _tmp_smaps | silent smap %s " % option +
                        "| redir END")

            # Check if any mappings where found
            all_maps = list(filter(len, eval(r"_tmp_smaps").splitlines()))
            if (len(all_maps) == 1 and all_maps[0][0] not in " sv"):
                # "No maps found". String could be localized. Hopefully
                # it doesn't start with any of these letters in any
                # language
                continue

            # Only keep mappings that should not be ignored
            maps = [m for m in all_maps if
                        not any(i in m for i in ignores) and len(m.strip())]

            for m in maps:
                # The first three chars are the modes, that might be listed.
                # We are not interested in them here.
                trig = m[3:].split()[0] if len(m[3:].split()) != 0 else None

                if trig is None:
                    continue

                # The bar separates commands
                if trig[-1] == "|":
                    trig = trig[:-1] + "<Bar>"

                # Special ones
                if trig[0] == "<":
                    add = False
                    # Only allow these
                    for valid in ["Tab", "NL", "CR", "C-Tab", "BS"]:
                        if trig == "<%s>" % valid:
                            add = True
                    if not add:
                        continue

                # UltiSnips remaps <BS>. Keep this around.
                if trig == "<BS>":
                    continue

                # Actually unmap it
                try:
                    command("silent! sunmap %s %s" % (option, trig))
                except:
                    # Bug 908139: ignore unmaps that fail because of
                    # unprintable characters. This is not ideal because we
                    # will not be able to unmap lhs with any unprintable
                    # character. If the lhs stats with a printable
                    # character this will leak to the user when he tries to
                    # type this character as a first in a selected tabstop.
                    # This case should be rare enough to not bother us
                    # though.
                    pass
# End:  Helper functions  }}}
# Helper classes  {{{
class _Real_LangMapTranslator(object):
    """
    This carse for the Vim langmap option and basically reverses the mappings. This
    was the only solution to get UltiSnips to work nicely with langmap; other stuff
    I tried was using inoremap movement commands and caching and restoring the
    langmap option.

    Note that this will not work if the langmap overwrites a character completely,
    for example if 'j' is remapped, but nothing is mapped back to 'j', then moving
    one line down is no longer possible and UltiSnips will fail.
    """
    _maps = {}
    _SEMICOLONS = re.compile(r"(?<!\\);")
    _COMMA = re.compile(r"(?<!\\),")

    def _create_translation(self, langmap):
        from_chars, to_chars = "", ""
        for c in self._COMMA.split(langmap):
            c = c.replace("\\,", ",")
            res = self._SEMICOLONS.split(c)
            if len(res) > 1:
                a,b = map(lambda a: a.replace("\\;", ";"), res)
                from_chars += a
                to_chars += b
            else:
                from_chars += c[::2]
                to_chars += c[1::2]
        self._maps[langmap] = (from_chars, to_chars)

    def translate(self, s):
        langmap = eval("&langmap").strip()
        if langmap == "":
            return s

        s = as_unicode(s)
        if langmap not in self._maps:
            self._create_translation(langmap)

        for f,t in zip(*self._maps[langmap]):
            s = s.replace(f,t)
        return s

class _Dummy_LangMapTranslator(object):
    """
    If vim hasn't got the langmap compiled in, we never have to do anything.
    Then this class is used.
    """
    translate = lambda self, s: s

_LangMapTranslator = _Real_LangMapTranslator
if not int(eval('has("langmap")')):
    _LangMapTranslator = _Dummy_LangMapTranslator
# End: Helper classes  }}}
