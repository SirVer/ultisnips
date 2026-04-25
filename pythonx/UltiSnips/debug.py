#!/usr/bin/env python3

"""Convenience methods that help with debugging.

Importing this module clears the dump file (default ``/tmp/file.txt`` on
Unix, ``C:/windows/temp/ultisnips.txt`` on Windows; override with the
``ULTISNIPS_DEBUG_PATH`` env var). Helpers append timestamped lines so
diffing a failing run against a control run pinpoints divergence.

Should not be used in production code.

Typical hunt for textobject corruption — drop calls at suspect sites such
as ``SnippetManager._jump``, ``SnippetManager._cursor_moved``,
``SnippetInstance.select_next_tab``, and the ``_active_snippets.append``
line in ``_do_snippet``::

    from UltiSnips.debug import debug, debug_section, debug_snippet_stack

    def _jump(self, jump_direction):
        debug_section(f"_jump dir={jump_direction!r}")
        debug_snippet_stack(self._active_snippets)
        ...

Run the failing test, then a control test with the suspected variable
removed (e.g. popup vs. no popup), and ``diff`` the two log files. The
first divergence is usually the smoking gun.

Remove the imports and calls before committing.
"""

import os
import sys
import time

DUMP_FILENAME = os.environ.get(
    "ULTISNIPS_DEBUG_PATH",
    "C:/windows/temp/ultisnips.txt"
    if sys.platform.lower().startswith("win")
    else "/tmp/file.txt",
)
_START = time.monotonic()
with open(DUMP_FILENAME, "w"):
    pass  # clears the file


def debug(msg):
    """Append ``msg`` to the debug file, prefixed with elapsed seconds."""
    elapsed = time.monotonic() - _START
    line = f"[{elapsed:7.3f}] {msg}\n"
    with open(DUMP_FILENAME, "ab") as dump_file:
        dump_file.write(line.encode("utf-8"))


def debug_section(label=""):
    """Append a 60-char ``=`` divider, optionally followed by a label."""
    debug("=" * 60)
    if label:
        debug(label)


def debug_snippet_stack(active_snippets):
    """Pretty-print the snippet stack: span, ``_cts``, tabstops.

    Reaches into private attributes (``_cts``, ``_tabstops``) — intended
    only for debugging.
    """
    for i, snip in enumerate(active_snippets):
        tabstops = ", ".join(
            f"{n}: {t.start}..{t.end}" for n, t in sorted(snip._tabstops.items())
        )
        debug(
            f"  snippet[{i}] _cts={snip._cts} "
            f"span={snip.start}..{snip.end} tabstops={{{tabstops}}}"
        )


def echo_to_hierarchy(text_object):
    """Outputs the given 'text_object' and its children hierarchically."""

    orig = text_object
    parent = text_object
    while parent._parent:
        parent = parent._parent

    def _do_print(text_object, indent=""):
        """prints recursively."""
        debug(indent + ("MAIN: " if text_object == orig else "") + str(text_object))
        try:
            for child in text_object._children:
                _do_print(child, indent=indent + "  ")
        except AttributeError:
            pass

    _do_print(parent)


def print_stack():
    """Dump a stack trace into the debug file."""
    import traceback

    with open(DUMP_FILENAME, "a") as dump_file:
        traceback.print_stack(file=dump_file)
