#!/usr/bin/env python
# encoding: utf-8

"""
This file contains object to care for the vim langmap option and basically
reverses the mappings. This was the only solution to get UltiSnips to work
nicely with langmap; other stuff I tried was using inoremap movement commands
and caching and restoring the langmap option.

Note that this will not work if the langmap overwrites a character completely,
for example if 'j' is remapped, but nothing is mapped back to 'j', then moving
one line down is no longer possible and UltiSnips will fail.
"""

import string

import vim

class Real_LangMapTranslator(object):
    """
    This is the object to deal with langmaps if this option is compiled
    into vim.
    """
    _maps = {}

    def _create_translation(self, langmap):
        from_chars, to_chars = "", ""
        for c in langmap.split(','):
            if ";" in c:
                a,b = c.split(';')
                from_chars += a
                to_chars += b
            else:
                from_chars += c[::2]
                to_chars += c[1::2]

        self._maps[langmap] = string.maketrans(to_chars, from_chars)

    def translate(self, s):
        langmap = vim.eval("&langmap").strip()
        if langmap == "":
            return s

        if langmap not in self._maps:
            self._create_translation(langmap)

        return s.translate(self._maps[langmap])

class Dummy_LangMapTranslator(object):
    """
    If vim hasn't got the langmap compiled in, we never have to do anything.
    Then this class is used.
    """
    translate = lambda self, s: s

LangMapTranslator = Real_LangMapTranslator
if not int(vim.eval('has("langmap")')):
    LangMapTranslator = Dummy_LangMapTranslator



