#!/usr/bin/env python
# encoding: utf-8

__all__ = [ "debug" ]

import types

from UltiSnips.compatibility import as_unicode

def echo_to_hierarchy(to):
    par = to
    while par._parent: par = par._parent

    def _do_print(to, indent=""):
        debug(indent + as_unicode(to))

        try:
            for c in to._childs:
                _do_print(c, indent=indent + "  ")
        except AttributeError:
            pass

    _do_print(par)

def debug(s):
    s = as_unicode(s)
    f = open("/tmp/file.txt","ab")
    f.write((s + '\n').encode("utf-8"))
    f.close()


