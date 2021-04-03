#!/usr/bin/env python3
# encoding: utf-8

"""Parses snipMate files."""

import os
import glob

from UltiSnips import vim_helper
from UltiSnips.snippet.definition import SnipMateSnippetDefinition
from UltiSnips.snippet.source.file.base import SnippetFileSource
from UltiSnips.snippet.source.file.common import handle_extends, normalize_file_path
from UltiSnips.text import LineIterator, head_tail


def _splitall(path):
    """Split 'path' into all its components."""
    # From http://my.safaribooksonline.com/book/programming/
    # python/0596001673/files/pythoncook-chp-4-sect-16
    allparts = []
    while True:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def _snipmate_files_for(ft):
    """Returns all snipMate files we need to look at for 'ft'."""
    if ft == "all":
        ft = "_"
    patterns = [
        "%s.snippets" % ft,
        os.path.join(ft, "*.snippets"),
        os.path.join(ft, "*.snippet"),
        os.path.join(ft, "*/*.snippet"),
    ]
    ret = set()
    for rtp in vim_helper.eval("&runtimepath").split(","):
        path = normalize_file_path(os.path.expanduser(os.path.join(rtp, "snippets")))
        for pattern in patterns:
            for fn in glob.glob(os.path.join(path, pattern)):
                ret.add(fn)
    return ret


def _parse_snippet_file(content, full_filename):
    """Parses 'content' assuming it is a .snippet file and yields events."""
    filename = full_filename[: -len(".snippet")]  # strip extension
    segments = _splitall(filename)
    segments = segments[segments.index("snippets") + 1 :]
    assert len(segments) in (2, 3)

    trigger = segments[1]
    description = segments[2] if 2 < len(segments) else ""

    # Chomp \n if any.
    if content and content.endswith(os.linesep):
        content = content[: -len(os.linesep)]
    yield "snippet", (
        SnipMateSnippetDefinition(trigger, content, description, full_filename),
    )


def _parse_snippet(line, lines, filename):
    """Parse a snippet defintions."""
    start_line_index = lines.line_index
    trigger, description = head_tail(line[len("snippet") :].lstrip())
    content = ""
    while True:
        next_line = lines.peek()
        if next_line is None:
            break
        if next_line.strip() and not next_line.startswith("\t"):
            break
        line = next(lines)
        if line[0] == "\t":
            line = line[1:]
        content += line
    content = content[:-1]  # Chomp the last newline
    return (
        "snippet",
        (
            SnipMateSnippetDefinition(
                trigger, content, description, "%s:%i" % (filename, start_line_index)
            ),
        ),
    )


def _parse_snippets_file(data, filename):
    """Parse 'data' assuming it is a .snippets file.

    Yields events in the file.

    """
    lines = LineIterator(data)
    for line in lines:
        if not line.strip():
            continue

        head, tail = head_tail(line)
        if head == "extends":
            yield handle_extends(tail, lines.line_index)
        elif head in "snippet":
            snippet = _parse_snippet(line, lines, filename)
            if snippet is not None:
                yield snippet
        elif head and not head.startswith("#"):
            yield "error", ("Invalid line %r" % line.rstrip(), lines.line_index)


class SnipMateFileSource(SnippetFileSource):

    """Manages all snipMate snippet definitions found in rtp."""

    def _get_all_snippet_files_for(self, ft):
        return _snipmate_files_for(ft)

    def _parse_snippet_file(self, filedata, filename):
        if filename.lower().endswith("snippet"):
            for event, data in _parse_snippet_file(filedata, filename):
                yield event, data
        else:
            for event, data in _parse_snippets_file(filedata, filename):
                yield event, data
