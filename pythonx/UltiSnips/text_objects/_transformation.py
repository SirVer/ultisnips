#!/usr/bin/env python
# encoding: utf-8

"""Implements TabStop transformations."""

import re
import sys

from UltiSnips.text import unescape, fill_in_whitespace
from UltiSnips.text_objects._mirror import Mirror


def _find_closing_brace(string, start_pos):
    """Finds the corresponding closing brace after start_pos."""
    bracks_open = 1
    for idx, char in enumerate(string[start_pos:]):
        if char == '(':
            if string[idx + start_pos - 1] != '\\':
                bracks_open += 1
        elif char == ')':
            if string[idx + start_pos - 1] != '\\':
                bracks_open -= 1
            if not bracks_open:
                return start_pos + idx + 1


def _split_conditional(string):
    """Split the given conditional 'string' into its arguments."""
    bracks_open = 0
    args = []
    carg = ''
    for idx, char in enumerate(string):
        if char == '(':
            if string[idx - 1] != '\\':
                bracks_open += 1
        elif char == ')':
            if string[idx - 1] != '\\':
                bracks_open -= 1
        elif char == ':' and not bracks_open and not string[idx - 1] == '\\':
            args.append(carg)
            carg = ''
            continue
        carg += char
    args.append(carg)
    return args


def _replace_conditional(match, string):
    """Replaces a conditional match in a transformation."""
    conditional_match = _CONDITIONAL.search(string)
    while conditional_match:
        start = conditional_match.start()
        end = _find_closing_brace(string, start + 4)
        args = _split_conditional(string[start + 4:end - 1])
        rv = ''
        if match.group(int(conditional_match.group(1))):
            rv = unescape(_replace_conditional(match, args[0]))
        elif len(args) > 1:
            rv = unescape(_replace_conditional(match, args[1]))
        string = string[:start] + rv + string[end:]
        conditional_match = _CONDITIONAL.search(string)
    return string

_ONE_CHAR_CASE_SWITCH = re.compile(r"\\([ul].)", re.DOTALL)
_LONG_CASEFOLDINGS = re.compile(r"\\([UL].*?)\\E", re.DOTALL)
_DOLLAR = re.compile(r"\$(\d+)", re.DOTALL)
_CONDITIONAL = re.compile(r"\(\?(\d+):", re.DOTALL)


class _CleverReplace(object):

    """Mimics TextMates replace syntax."""

    def __init__(self, expression):
        self._expression = expression

    def replace(self, match):
        """Replaces 'match' through the correct replacement string."""
        transformed = self._expression
        # Replace all $? with capture groups
        transformed = _DOLLAR.subn(
            lambda m: match.group(int(m.group(1))), transformed)[0]

        # Replace Case switches
        def _one_char_case_change(match):
            """Replaces one character case changes."""
            if match.group(1)[0] == 'u':
                return match.group(1)[-1].upper()
            else:
                return match.group(1)[-1].lower()
        transformed = _ONE_CHAR_CASE_SWITCH.subn(
            _one_char_case_change, transformed)[0]

        def _multi_char_case_change(match):
            """Replaces multi character case changes."""
            if match.group(1)[0] == 'U':
                return match.group(1)[1:].upper()
            else:
                return match.group(1)[1:].lower()
        transformed = _LONG_CASEFOLDINGS.subn(
            _multi_char_case_change, transformed)[0]
        transformed = _replace_conditional(match, transformed)
        return unescape(fill_in_whitespace(transformed))

# flag used to display only one time the lack of unidecode
UNIDECODE_ALERT_RAISED = False


class TextObjectTransformation(object):

    """Base class for Transformations and ${VISUAL}."""

    def __init__(self, token):
        self._convert_to_ascii = False

        self._find = None
        if token.search is None:
            return

        flags = 0
        self._match_this_many = 1
        if token.options:
            if 'g' in token.options:
                self._match_this_many = 0
            if 'i' in token.options:
                flags |= re.IGNORECASE
            if 'a' in token.options:
                self._convert_to_ascii = True

        self._find = re.compile(token.search, flags | re.DOTALL)
        self._replace = _CleverReplace(token.replace)

    def _transform(self, text):
        """Do the actual transform on the given text."""
        global UNIDECODE_ALERT_RAISED  # pylint:disable=global-statement
        if self._convert_to_ascii:
            try:
                import unidecode
                text = unidecode.unidecode(text)
            except Exception:  # pylint:disable=broad-except
                if UNIDECODE_ALERT_RAISED == False:
                    UNIDECODE_ALERT_RAISED = True
                    sys.stderr.write(
                        'Please install unidecode python package in order to '
                        'be able to make ascii conversions.\n')
        if self._find is None:
            return text
        return self._find.subn(
            self._replace.replace, text, self._match_this_many)[0]


class Transformation(Mirror, TextObjectTransformation):

    """See module docstring."""

    def __init__(self, parent, ts, token):
        Mirror.__init__(self, parent, ts, token)
        TextObjectTransformation.__init__(self, token)

    def _get_text(self):
        return self._transform(self._ts.current_text)
