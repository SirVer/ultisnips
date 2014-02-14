#!/usr/bin/env python
# encoding: utf-8

"""Parsing of snippet files."""

from collections import defaultdict

class _LineIterator(object):
    """Convenience class that keeps track of line numbers."""

    def __init__(self, text):
        self._line_index = None
        self._lines = enumerate(text.splitlines(True), 1)

    def __iter__(self):
        return self

    def __next__(self):
        """Returns the next line."""
        self._line_index, line = next(self._lines)
        return line
    next = __next__  # for python2

    @property
    def line_index(self):
        """The 1 based line index in the current file."""
        return self._line_index

def _handle_snippet_or_global(line, lines, globals):
    """Parses the snippet that begins at the current line."""

    descr = ""
    opts = ""

    # Ensure this is a snippet
    snip = line.split()[0]

    # Get and strip options if they exist
    remain = line[len(snip):].strip()
    words = remain.split()
    if len(words) > 2:
        # second to last word ends with a quote
        if '"' not in words[-1] and words[-2][-1] == '"':
            opts = words[-1]
            remain = remain[:-len(opts) - 1].rstrip()

    # Get and strip description if it exists
    remain = remain.strip()
    if len(remain.split()) > 1 and remain[-1] == '"':
        left = remain[:-1].rfind('"')
        if left != -1 and left != 0:
            descr, remain = remain[left:], remain[:left]

    # The rest is the trigger
    trig = remain.strip()
    if len(trig.split()) > 1 or "r" in opts:
        if trig[0] != trig[-1]:
            return "error", ("Invalid multiword trigger: '%s'" % trig,
                    lines.line_index)
        trig = trig[1:-1]
    end = "end" + snip
    content = ""

    found_end = False
    for line in lines:
        if line.rstrip() == end:
            content = content[:-1]  # Chomp the last newline
            found_end = True
            break
        content += line

    if not found_end:
        return "error", ("Missing 'endsnippet' for %r" % trig, lines.line_index)

    if snip == "global":
        globals[trig].append(content)
    elif snip == "snippet":
        return "snippet", (trig, content, descr, opts, globals)
    else:
        return "error", ("Invalid snippet type: '%s'" % snip, lines.line_index)

def _head_tail(line):
    """Returns the first word in 'line' and the rest of 'line' or None if the
    line is too short."""
    generator = (t.strip() for t in line.split(None, 1))
    head = next(generator).strip()
    tail = ''
    try:
        tail = next(generator).strip()
    except StopIteration:
        pass
    return head, tail


def parse_snippets_file(data):
    """Parse 'data' assuming it is a snippet file. Yields events in the
    file."""

    globals = defaultdict(list)
    lines = _LineIterator(data)
    for line in lines:
        if not line.strip():
            continue

        head, tail = _head_tail(line)
        if head == "extends":
            if tail:
                yield "extends", ([p.strip() for p in tail.split(',')],)
            else:
                yield "error", ("'extends' without file types",
                        lines.line_index)
        elif head in ("snippet", "global"):
            snippet = _handle_snippet_or_global(line, lines, globals)
            if snippet is not None:
                yield snippet
        elif head == "clearsnippets":
            yield "clearsnippets", (tail.split(),)
        elif head and not head.startswith('#'):
            yield "error", ("Invalid line %r" % line.rstrip(), lines.line_index)
