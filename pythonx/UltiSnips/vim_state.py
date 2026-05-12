#!/usr/bin/env python3

"""Some classes to conserve Vim's state for comparing over time."""

from collections import deque
from typing import NamedTuple

import vim

from UltiSnips import vim_helper
from UltiSnips.position import Position
from UltiSnips.vim_encoding import byte2col


def _vim_str(s):
    """Render a Python string as a single-quoted Vim string literal."""
    return "'" + s.replace("'", "''") + "'"


class _Placeholder(NamedTuple):
    current_text: str
    start: Position
    end: Position


class VimPosition(Position):
    """Represents the current position in the buffer, together with some status
    variables that might change our decisions down the line."""

    def __init__(self):
        pos = vim_helper.buf.cursor
        self._mode = vim_helper.eval("mode()")
        super().__init__(pos.line, pos.col)

    @property
    def mode(self):
        """Returns the mode() this position was created."""
        return self._mode


class VimState:
    """Caches some state information from Vim to better guess what editing
    tasks the user might have done in the last step."""

    # Registers preserved across snippet expansion. Iteration order is the
    # restore order: @- and @1-@9 are written first because setreg on those
    # only touches the target register; @0 is next because setreg('0', …)
    # re-points the unnamed register at @0; @" is last so its points-to
    # alias ends up where it was pre-snippet. The unnamed register `"`
    # appears in the iterable for caching but is handled specially on
    # restore via setreg with the cached reginfo dict.
    _PRESERVED_REGISTERS = ("-", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", '"')

    def __init__(self):
        self._poss = deque(maxlen=5)
        self._lvb = None

        self._text_to_expect = ""

        # Cache reginfo dicts for each preserved register in a Vim variable
        # so binary register contents (which can't always cross the
        # Python/Vim string boundary) survive cleanly. An empty dict means
        # "nothing to restore" — populated on first remember during a
        # snippet, cleared at teardown.
        vim.command("let g:_ultisnips_reg_cache = {}")

    def remember_unnamed_register(self, text_to_expect):
        """Cache the snippet-clobberable registers if @" doesn't already
        match the previously-expected text.

        'text_to_expect' is text we expect to be in @" on the next call
        (typically the placeholder text the snippet just put there). When
        @" still matches the previous expectation we know we put it there
        ourselves, so we don't overwrite the original cached state.

        """
        escaped_text = self._text_to_expect.replace("'", "''")
        res = int(vim_helper.eval('@" != ' + "'" + escaped_text + "'"))
        if res:
            for reg in self._PRESERVED_REGISTERS:
                lit = _vim_str(reg)
                vim.command(f"let g:_ultisnips_reg_cache[{lit}] = getreginfo({lit})")
        self._text_to_expect = text_to_expect

    def restore_unnamed_register(self):
        """Restore the cached registers, if we have any cached.

        Iteration order matters because `setreg('0', …)` and
        `setreg('"', dict)` both update the unnamed-register pointer.
        We restore @- and @1-@9 first (those only touch the target
        register), then @0 (which re-points @" to @0), then @" last
        with its cached reginfo dict — `setreg('"', dict)` honours
        the dict's `points_to` and writes the value into whichever
        register the pointer aliased pre-snippet, leaving the others
        intact (pre-snippet `@"` and its alias-target hold the same
        value, so this is content-neutral for the alias target).

        Restore is idempotent — running it twice in a row gives the
        same end state. The cache itself is only cleared in
        :meth:`reset_cache`, called from teardown.

        """
        if int(vim_helper.eval("empty(g:_ultisnips_reg_cache)")):
            return
        for reg in self._PRESERVED_REGISTERS:
            lit = _vim_str(reg)
            vim.command(
                f"if has_key(g:_ultisnips_reg_cache, {lit}) | "
                f"call setreg({lit}, g:_ultisnips_reg_cache[{lit}]) | "
                f"endif"
            )

    def reset_register_cache(self):
        """Drop the cached register state. Called when the snippet
        finishes so the next one starts from a clean slate."""
        vim.command("let g:_ultisnips_reg_cache = {}")
        self._text_to_expect = ""

    def remember_position(self):
        """Remember the current position as a previous pose."""
        self._poss.append(VimPosition())

    def remember_buffer(self, to):
        """Remember the content of the buffer and the position."""
        self._lvb = vim_helper.buf[to.start.line : to.end.line + 1]
        self._lvb_len = len(vim_helper.buf)
        self.remember_position()

    @property
    def pos(self):
        """The last remembered position."""
        return self._poss[-1]

    @property
    def ppos(self):
        """The second to last remembered position."""
        return self._poss[-2]

    @property
    def remembered_buffer(self):
        """The content of the remembered buffer."""
        return self._lvb[:]

    @property
    def remembered_buffer_length(self):
        """The total buffer length when the buffer was last remembered."""
        return self._lvb_len


class VisualContentPreserver:
    """Saves the current visual selection and the selection mode it was done in
    (e.g. line selection, block selection or regular selection.)"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Forget the preserved state."""
        self._mode = ""
        self._text = ""
        self._placeholder = None

    def conserve(self):
        """Save the last visual selection and the mode it was made in."""
        sl, sbyte = map(
            int, (vim_helper.eval("""line("'<")"""), vim_helper.eval("""col("'<")"""))
        )
        el, ebyte = map(
            int, (vim_helper.eval("""line("'>")"""), vim_helper.eval("""col("'>")"""))
        )
        sc = byte2col(sl, sbyte - 1)
        ec = byte2col(el, ebyte - 1)
        self._mode = vim_helper.eval("visualmode()")

        # When 'selection' is 'exclusive', the > mark is one column behind the
        # actual content being copied, but never before the < mark.
        if vim_helper.eval("&selection") == "exclusive" and not (
            sl == el and sbyte == ebyte
        ):
            ec -= 1

        _vim_line_with_eol = lambda ln: vim_helper.buf[ln] + "\n"

        if sl == el:
            text = _vim_line_with_eol(sl - 1)[sc : ec + 1]
        else:
            text = _vim_line_with_eol(sl - 1)[sc:]
            for cl in range(sl, el - 1):
                text += _vim_line_with_eol(cl)
            text += _vim_line_with_eol(el - 1)[: ec + 1]
        self._text = text

    def conserve_placeholder(self, placeholder):
        if placeholder:
            self._placeholder = _Placeholder(
                placeholder.current_text, placeholder.start, placeholder.end
            )
        else:
            self._placeholder = None

    @property
    def text(self):
        """The conserved text."""
        return self._text

    @property
    def mode(self):
        """The conserved visualmode()."""
        return self._mode

    @property
    def placeholder(self):
        """Returns latest selected placeholder."""
        return self._placeholder
