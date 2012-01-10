#!/usr/bin/env python
# encoding: utf-8


"""
This file contains code that is invalid in python3 and must therefore never be
seen by the interpretor
"""

def compatible_exec(code, gglobals = None, glocals = None):
    if gglobals is not None and glocals is not None:
        exec code in gglobals, glocals
    elif gglobals is not None:
        exec code in gglobals
    else:
        exec code


