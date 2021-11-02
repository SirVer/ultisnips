#!/usr/bin/env python3
# encoding: utf-8

from enum import Enum


class JumpDirection(Enum):
    FORWARD = 1
    BACKWARD = 2


class Position:
    """Represents a Position in a text file: (0 based line index, 0 based column
    index, z to order Positions at the same locations) and provides methods for moving them around."""

    def __init__(self, line, col, z=0):
        self.line = line
        self.col = col
        self.z = z

    def move(self, pivot, delta):
        """'pivot' is the position of the first changed character, 'delta' is
        how text after it moved. Return True if the position has been deleted"""
        
        if pivot.line <= self.line :
            if pivot.line == self.line :
                if pivot.col <= self.col :
                    if pivot.col == self.col :
                        if pivot.z <= self.z :
                            self.z += pivot.z
                        elif pivot.z + delta.z < self.z :
                            return True
                    self.col += delta.col
                elif pivot.col + delta.col < self.col :
                    return True
            self.line += delta.line
        elif pivot.line + delta.line < self.line :
            return True
        return False
                    
    @property
    def tuple(self):
        return (self.line, self.col, self.z)

    def __iter__(self):
        return self.tuple.__iter__()

    def __add__(self, pos):
        assert isinstance(pos, Position)
        return Position(self.line + pos.line, self.col + pos.col, self.z + pos.z)

    def __sub__(self, pos):
        assert isinstance(pos, Position)
        return Position(self.line - pos.line, self.col - pos.col, self.z - pos.z)

    def __eq__(self, other):
        return self.tuple == other.tuple

    def __ne__(self, other):
        return self.tuple != other.tuple

    def __lt__(self, other):
        return self.tuple < other.tuple

    def __le__(self, other):
        return self.tuple <= other.tuple

    def __neg__(self):
        return Position(-self.line, -self.col, -self.z)
      
    def __repr__(self):
        return "(%i,%i,%i)" % self.tuple

    def __getitem__(self, index):
        if not (0 <=  index < 3):
            raise IndexError("position can be indexed only 0 (line), 1 (column) and 2 (z)")
        return self.tuple[index]

    def get_text_end(self, text):
        """Calculate the end position of the 'text' (list of lines) starting at self."""
        if len(text) == 1:
            new_end = self + Position(0, len(text[0]))
        else:
            new_end = Position(self.line + len(text) - 1, len(text[-1]))
        return new_end
        

    @classmethod
    def zero(cls):
      return Position(0, 0)

    @classmethod
    def _create_pivot_delta_for_edit_cmd(cls, cmd):
        """
        Create the delta between the cursor position in the command
        and the resulting position after
        """
        ctype, line, col, text = cmd
        delta = (
            Position(1, -col) # new line inserted, then cursor go at line start
            if text == '\n' else
            Position(0, len(text)) # Only the column moves
        )
        start = Position(line, col)
        if ctype == 'I' :
            return start, delta
        else :
            return start + delta, -delta
          
    @classmethod
    def _create_pivot_delta_for_line_change(cls, change):
        """
        Create the delta for a full line removal
        """
        ctype, line, _, text, *_ = change # col should be 0...
        start = Position(line, 0)
        delta = Position(1, 0)
        if ctype == 'I' :
            return start, delta
        else :
            return start + delta, -delta

    @classmethod
    def _create_edit_start_end_pos(cls, line, col, text):
        start = Position(line, col)
        end = (
            Position(line + 1, 0)
            if text == '\n' else
            Position(line, col + len(text))
        )
        return start, end

    @classmethod
    def _create_same_line_pivot_delta(cls, line, col_old, col_new):
        return Position(line, col_old), Position(0, col_new - col_old)
          
