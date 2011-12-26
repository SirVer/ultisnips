#!/usr/bin/env python
# encoding: utf-8

__all__ = [ "debug" ]

import types

def debug(s):
    if not isinstance(s, types.UnicodeType):
        s = s.decode("utf-8")
    f = open("/tmp/file.txt","a")
    f.write(s.encode("utf-8")+'\n')
    f.close()


