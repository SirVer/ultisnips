#!/usr/bin/env python
# encoding: utf-8

"""Utilities to deal with text escaping."""

def unescape(text):
    """Removes '\\' escaping from 'text'."""
    rv = ""
    i = 0
    while i < len(text):
        if i+1 < len(text) and text[i] == '\\':
            rv += text[i+1]
            i += 1
        else:
            rv += text[i]
        i += 1
    return rv

def fill_in_whitespace(text):
    """Returns 'text' with escaped whitespace replaced through whitespaces."""
    text = text.replace(r"\n", "\n")
    text = text.replace(r"\t", "\t")
    text = text.replace(r"\r", "\r")
    text = text.replace(r"\a", "\a")
    text = text.replace(r"\b", "\b")
    return text
