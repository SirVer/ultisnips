#!/usr/bin/env python
# encoding: utf-8

import re

from UltiSnips.text_objects._mirror import Mirror

class _CleverReplace(object):
    """
    This class mimics TextMates replace syntax
    """
    _DOLLAR = re.compile(r"\$(\d+)", re.DOTALL)
    _SIMPLE_CASEFOLDINGS = re.compile(r"\\([ul].)", re.DOTALL)
    _LONG_CASEFOLDINGS = re.compile(r"\\([UL].*?)\\E", re.DOTALL)
    _CONDITIONAL = re.compile(r"\(\?(\d+):", re.DOTALL)

    _UNESCAPE = re.compile(r'\\[^ntrab]')
    _SCHARS_ESCPAE = re.compile(r'\\[ntrab]')

    def __init__(self, s):
        self._s = s

    def _scase_folding(self, m):
        if m.group(1)[0] == 'u':
            return m.group(1)[-1].upper()
        else:
            return m.group(1)[-1].lower()
    def _lcase_folding(self, m):
        if m.group(1)[0] == 'U':
            return m.group(1)[1:].upper()
        else:
            return m.group(1)[1:].lower()

    def _replace_conditional(self, match, v):
        def _find_closingbrace(v,start_pos):
            bracks_open = 1
            for idx, c in enumerate(v[start_pos:]):
                if c == '(':
                    if v[idx+start_pos-1] != '\\':
                        bracks_open += 1
                elif c == ')':
                    if v[idx+start_pos-1] != '\\':
                        bracks_open -= 1
                    if not bracks_open:
                        return start_pos+idx+1
        m = self._CONDITIONAL.search(v)

        def _part_conditional(v):
            bracks_open = 0
            args = []
            carg = ""
            for idx, c in enumerate(v):
                if c == '(':
                    if v[idx-1] != '\\':
                        bracks_open += 1
                elif c == ')':
                    if v[idx-1] != '\\':
                        bracks_open -= 1
                elif c == ':' and not bracks_open and not v[idx-1] == '\\':
                    args.append(carg)
                    carg = ""
                    continue
                carg += c
            args.append(carg)
            return args

        while m:
            start = m.start()
            end = _find_closingbrace(v,start+4)
            args = _part_conditional(v[start+4:end-1])

            rv = ""
            if match.group(int(m.group(1))):
                rv = self._unescape(self._replace_conditional(match,args[0]))
            elif len(args) > 1:
                rv = self._unescape(self._replace_conditional(match,args[1]))

            v = v[:start] + rv + v[end:]

            m = self._CONDITIONAL.search(v)
        return v

    def _unescape(self, v):
        return self._UNESCAPE.subn(lambda m: m.group(0)[-1], v)[0]
    def _schar_escape(self, v):
        return self._SCHARS_ESCPAE.subn(lambda m: eval(r"'\%s'" % m.group(0)[-1]), v)[0]

    def replace(self, match):
        start, end = match.span()

        tv = self._s

        # Replace all $? with capture groups
        tv = self._DOLLAR.subn(lambda m: match.group(int(m.group(1))), tv)[0]

        # Replace CaseFoldings
        tv = self._SIMPLE_CASEFOLDINGS.subn(self._scase_folding, tv)[0]
        tv = self._LONG_CASEFOLDINGS.subn(self._lcase_folding, tv)[0]
        tv = self._replace_conditional(match, tv)

        return self._unescape(self._schar_escape(tv))

class TextObjectTransformation(object):
    def __init__(self, token):
        self._find = None
        if token.search is None:
            return

        flags = 0
        self._match_this_many = 1
        if token.options:
            if "g" in token.options:
                self._match_this_many = 0
            if "i" in token.options:
                flags |= re.IGNORECASE

        self._find = re.compile(token.search, flags | re.DOTALL)
        self._replace = _CleverReplace(token.replace)

    def _transform(self, text):
        if self._find is None:
            return text
        return self._find.subn(self._replace.replace, text, self._match_this_many)[0]

class Transformation(Mirror, TextObjectTransformation):
    def __init__(self, parent, ts, token):
        Mirror.__init__(self, parent, ts, token)
        TextObjectTransformation.__init__(self, token)

    def _get_text(self):
        return self._transform(self._ts.current_text)


