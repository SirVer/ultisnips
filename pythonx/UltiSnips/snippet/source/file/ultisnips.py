#!/usr/bin/env python
# encoding: utf-8

"""Parsing of snippet files."""

from collections import defaultdict
import glob
import os

from UltiSnips import _vim
from UltiSnips.snippet.definition import UltiSnipsSnippetDefinition
from UltiSnips.snippet.source.file._base import SnippetFileSource
from UltiSnips.snippet.source.file._common import handle_extends
from UltiSnips.text import LineIterator, head_tail

def find_snippet_files(ft, directory):
    """Returns all matching snippet files for 'ft' in 'directory'."""
    patterns = ["%s.snippets", "%s_*.snippets", os.path.join("%s", "*")]
    ret = set()
    directory = os.path.expanduser(directory)
    for pattern in patterns:
        for fn in glob.glob(os.path.join(directory, pattern % ft)):
            ret.add(os.path.realpath(fn))
    return ret

def find_all_snippet_files(ft):
    """Returns all snippet files matching 'ft' in the given runtime path
    directory."""
    if _vim.eval("exists('b:UltiSnipsSnippetDirectories')") == "1":
        snippet_dirs = _vim.eval("b:UltiSnipsSnippetDirectories")
    else:
        snippet_dirs = _vim.eval("g:UltiSnipsSnippetDirectories")

    patterns = ["%s.snippets", "%s_*.snippets", os.path.join("%s", "*")]
    ret = set()
    for rtp in _vim.eval("&runtimepath").split(','):
        for snippet_dir in snippet_dirs:
            if snippet_dir == "snippets":
                raise RuntimeError(
                    "You have 'snippets' in UltiSnipsSnippetDirectories. This "
                    "directory is reserved for snipMate snippets. Use another "
                    "directory for UltiSnips snippets.")
            pth = os.path.realpath(os.path.expanduser(
                os.path.join(rtp, snippet_dir)))
            for pattern in patterns:
                for fn in glob.glob(os.path.join(pth, pattern % ft)):
                    ret.add(fn)
    return ret

def _handle_snippet_or_global(filename, line, lines, python_globals, priority):
    """Parses the snippet that begins at the current line."""
    start_line_index = lines.line_index
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
        python_globals[trig].append(content)
    elif snip == "snippet":
        return "snippet", (UltiSnipsSnippetDefinition(priority, trig, content,
            descr, opts, python_globals,
            "%s:%i" % (filename, start_line_index)),)
    else:
        return "error", ("Invalid snippet type: '%s'" % snip, lines.line_index)

def _parse_snippets_file(data, filename):
    """Parse 'data' assuming it is a snippet file. Yields events in the
    file."""

    python_globals = defaultdict(list)
    lines = LineIterator(data)
    current_priority = 0
    for line in lines:
        if not line.strip():
            continue

        head, tail = head_tail(line)
        if head in ("snippet", "global"):
            snippet = _handle_snippet_or_global(filename, line, lines,
                    python_globals, current_priority)
            if snippet is not None:
                yield snippet
        elif head == "extends":
            yield handle_extends(tail, lines.line_index)
        elif head == "clearsnippets":
            yield "clearsnippets", (tail.split(),)
        elif head == "priority":
            try:
                current_priority = int(tail.split()[0])
            except (ValueError, IndexError):
                yield "error", ("Invalid priority %r" % tail, lines.line_index)
        elif head and not head.startswith('#'):
            yield "error", ("Invalid line %r" % line.rstrip(), lines.line_index)

class UltiSnipsFileSource(SnippetFileSource):
    """Manages all snippets definitions found in rtp for ultisnips."""

    def _get_all_snippet_files_for(self, ft):
        return find_all_snippet_files(ft)

    def _parse_snippet_file(self, filedata, filename):
        for event, data in _parse_snippets_file(filedata, filename):
            yield event, data
