#!/usr/bin/env python
# encoding: utf-8

__all__ = [ "debug" ]

import types

from UltiSnips.Compatibility import as_unicode

def debug(s):
    s = as_unicode(s)
    f = open("/tmp/file.txt","ab")
    f.write((s + '\n').encode("utf-8"))
    f.close()


