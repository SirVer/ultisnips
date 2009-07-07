#!/usr/bin/env python
# encoding: utf-8

__all__ = [ "debug" ]

def debug(s):
    f = open("/tmp/file.txt","a")
    f.write(s+'\n')
    f.close()


