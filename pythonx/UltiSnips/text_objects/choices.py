#!/usr/bin/env python
# encoding: utf-8

"""Choices are enumeration values you can choose, by selecting index number.
It is a special TabStop, its content are taken literally, thus said, they will not be parsed recursively.
"""

from UltiSnips import vim_helper
from UltiSnips.position import Position
from UltiSnips.text_objects.tabstop import TabStop
from UltiSnips.snippet.parsing.lexer import ChoicesToken


class Choices(TabStop):
    """See module docstring."""
    def __init__(self, parent, token: ChoicesToken):
        self._number = token.number  # for TabStop property 'number'
        self._initial_text = token.initial_text

        # empty choice will be discarded
        self._choice_list = [s for s in token.choice_list if len(s) > 0]
        self._done = False
        self._input_chars = list(self._initial_text)
        self._has_been_updated = False

        TabStop.__init__(self, parent, token)

    def _get_choices_placeholder(self) -> str:
        # prefix choices with index number
        # e.g. 'a,b,c' -> '1.a|2.b|3.c'
        text_segs = []
        index = 1
        for choice in self._choice_list:
            text_segs.append("%s.%s" % (index, choice))
            index += 1
        text = "|".join(text_segs)
        return text

    def _update(self, done, buf):
        if self._done:
            return True

        # expand initial text with select prefix number, only once
        if not self._has_been_updated:
            # '${1:||}' is not valid choice, should be downgraded to plain tabstop
            are_choices_valid = len(self._choice_list) > 0
            if are_choices_valid:
                text = self._get_choices_placeholder()
                self.overwrite(buf, text)
            else:
                self._done = True
            self._has_been_updated = True
        return True

    def _do_edit(self, cmd, ctab=None):
        if self._done:
            # do as what parent class do
            TabStop._do_edit(self, cmd, ctab)
            return

        ctype, line, col, cmd_text = cmd

        cursor = vim_helper.get_cursor_pos()
        [buf_num, cursor_line] = map(int, cursor[0:2])

        # trying to get what user inputted in current buffer
        if ctype == "I":
            self._input_chars.append(cmd_text)
        elif ctype == "D":
            line_text = vim_helper.buf[cursor_line - 1]
            self._input_chars = list(line_text[self._start.col: col])

        inputted_text = "".join(self._input_chars)

        if not self._input_chars:
            return

        # if there are more than 9 selection candidates,
        # may need to wait for 2 inputs to determine selection number
        is_all_digits = True
        has_selection_terminator = False

        # input string sub string of pure digits
        inputted_text_for_num = inputted_text
        for [i, s] in enumerate(self._input_chars):
            if s == " ":  # treat space as a terminator for selection
                has_selection_terminator = True
                inputted_text_for_num = inputted_text[0:i]
            elif not s.isdigit():
                is_all_digits = False

        should_continue_input = False
        if is_all_digits or has_selection_terminator:
            index_strs = [str(index) for index in list(range(1, len(self._choice_list) + 1))]
            matched_index_strs = list(filter(lambda s: s.startswith(inputted_text_for_num), index_strs))
            remained_choice_list = []
            if len(matched_index_strs) == 0:
                remained_choice_list = []
            elif has_selection_terminator:
                if inputted_text_for_num:
                    num = int(inputted_text_for_num)
                    remained_choice_list = list(self._choice_list)[num - 1: num]
            elif len(matched_index_strs) == 1:
                num = int(inputted_text_for_num)
                remained_choice_list = list(self._choice_list)[num - 1: num]
            else:
                should_continue_input = True
        else:
            remained_choice_list = []

        if should_continue_input:
            # will wait for further input
            return

        buf = vim_helper.buf
        if len(remained_choice_list) == 0:
            # no matched choice, should quit selection and go on with inputted text
            overwrite_text = inputted_text_for_num
            self._done = True
        elif len(remained_choice_list) == 1:
            # only one match
            matched_choice = remained_choice_list[0]
            overwrite_text = matched_choice
            self._done = True

        if overwrite_text is not None:
            old_end_col = self._end.col

            # change _end.col, thus `overwrite` won't alter texts after this tabstop
            displayed_text_end_col = self._start.col + len(inputted_text)
            self._end.col = displayed_text_end_col
            self.overwrite(buf, overwrite_text)

            # notify all tabstops those in the same line and after this to adjust their positions
            pivot = Position(line, old_end_col)
            diff_col = displayed_text_end_col - old_end_col
            self._parent._child_has_moved(
                self._parent.children.index(self),
                pivot,
                Position(0, diff_col)
            )

            vim_helper.set_cursor_from_pos([buf_num, cursor_line, self._end.col + 1])

    def __repr__(self):
        return "Choices(%s,%r->%r,%r)" % (self._number, self._start, self._end, self._initial_text)
