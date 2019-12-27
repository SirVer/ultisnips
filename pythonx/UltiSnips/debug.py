#!/usr/bin/env python
# encoding: utf-8

"""Convenience methods that help with debugging.

They should never be used in production code.

"""

import sys

DUMP_FILENAME = (
    "/tmp/file.txt"
    if not sys.platform.lower().startswith("win")
    else "C:/windows/temp/ultisnips.txt"
)
with open(DUMP_FILENAME, "w"):
    pass  # clears the file


def echo_to_hierarchy(text_object):
    """Outputs the given 'text_object' and its children hierarchically."""
    # pylint:disable=protected-access
    parent = text_object
    while parent._parent:
        parent = parent._parent

    def _do_print(text_object, indent=""):
        """prints recursively."""
        debug(indent + text_object)
        try:
            for child in text_object._children:
                _do_print(child, indent=indent + "  ")
        except AttributeError:
            pass

    _do_print(parent)


def debug(msg):
    """Dumb 'msg' into the debug file."""
    with open(DUMP_FILENAME, "ab") as dump_file:
        dump_file.write((msg + "\n").encode("utf-8"))


def print_stack():
    """Dump a stack trace into the debug file."""
    import traceback

    with open(DUMP_FILENAME, "ab") as dump_file:
        traceback.print_stack(file=dump_file)
