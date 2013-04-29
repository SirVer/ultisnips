#!/usr/bin/env python
# encoding: utf-8

__all__ = [ "debug", "echo_to_hierarchy", "print_stack" ]

import sys
import os

from UltiSnips.compatibility import as_unicode
if sys.platform.lower().startswith("win"):
    dump_filename = "C:/windows/temp/ultisnips.log"
elif sys.platform.lower().startswith("darwin"):
    dump_filename = os.path.expanduser("~/Library/Logs/ultisnips.log")
else:
    dump_filename = "/var/log/ultisnips.log"

with open(dump_filename, "w") as dump_file:
    pass # clears the file

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
    with open(dump_filename, "ab") as dump_file:
        dump_file.write((s + '\n').encode("utf-8"))

def print_stack():
    import traceback
    with open(dump_filename, "ab") as dump_file:
        traceback.print_stack(file=dump_file)

