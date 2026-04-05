#!/usr/bin/env python3

"""Parsing of snippet files."""

from collections import defaultdict
from pathlib import Path

from UltiSnips import vim_helper
from UltiSnips.error import PebkacError
from UltiSnips.snippet.definition import UltiSnipsSnippetDefinition
from UltiSnips.snippet.source.file.base import SnippetFileSource
from UltiSnips.snippet.source.file.common import (
    handle_action,
    handle_context,
    handle_extends,
    normalize_file_path,
)
from UltiSnips.text import LineIterator, head_tail


def find_snippet_files(ft, directory: str) -> set[str]:
    """Returns all matching snippet files for 'ft' in 'directory'."""
    patterns = ["%s.snippets", "%s_*.snippets", str(Path("%s") / "*")]
    ret = set()
    directory_path = Path(directory).expanduser()
    for pattern in patterns:
        for fn in directory_path.glob(pattern % ft):
            ret.add(normalize_file_path(str(fn)))
    return ret


def find_all_snippet_directories() -> list[str]:
    """Returns a list of the absolute path of all potential snippet
    directories, no matter if they exist or not."""

    if vim_helper.eval("exists('b:UltiSnipsSnippetDirectories')") == "1":
        snippet_dirs = vim_helper.eval("b:UltiSnipsSnippetDirectories")
    else:
        snippet_dirs = vim_helper.eval("g:UltiSnipsSnippetDirectories")

    if len(snippet_dirs) == 1:
        # To reduce confusion and increase consistency with
        # `UltiSnipsSnippetsDir`, we expand ~ here too.
        full_path = Path(snippet_dirs[0]).expanduser()
        if full_path.is_absolute():
            return [str(full_path)]

    all_dirs = []
    check_dirs = vim_helper.eval("&runtimepath").split(",")
    for rtp in check_dirs:
        for snippet_dir in snippet_dirs:
            if snippet_dir == "snippets":
                raise PebkacError(
                    "You have 'snippets' in UltiSnipsSnippetDirectories. This "
                    "directory is reserved for snipMate snippets. Use another "
                    "directory for UltiSnips snippets."
                )
            pth = Path(rtp, snippet_dir).expanduser()
            # Runtimepath entries may contain wildcards.
            all_dirs.extend(
                str(p) for p in Path(pth.anchor).glob(str(pth.relative_to(pth.anchor)))
            )
    return all_dirs


def find_all_snippet_files(ft) -> set[str]:
    """Returns all snippet files matching 'ft' in the given runtime path
    directory."""
    patterns = ["%s.snippets", "%s_*.snippets", str(Path("%s") / "*")]
    ret = set()
    for directory in find_all_snippet_directories():
        if not Path(directory).is_dir():
            continue
        for pattern in patterns:
            for fn in Path(directory).glob(pattern % ft):
                ret.add(str(fn))
    return ret


def _handle_snippet_or_global(
    filename, line, lines, python_globals, priority, pre_expand, context
):
    """Parses the snippet that begins at the current line."""
    start_line_index = lines.line_index
    descr = ""
    opts = ""

    # Ensure this is a snippet
    snip = line.split()[0]

    # Get and strip options if they exist
    remain = line[len(snip) :].strip()
    words = remain.split()

    # second to last word ends with a quote
    if len(words) > 2 and '"' not in words[-1] and words[-2][-1] == '"':
        opts = words[-1]
        remain = remain[: -len(opts) - 1].rstrip()

    if "e" in opts and not context:
        left = remain[:-1].rfind('"')
        if left != -1 and left != 0:
            context, remain = remain[left:].strip('"'), remain[:left]

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
            return "error", (f"Invalid multiword trigger: '{trig}'", lines.line_index)
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
        return "error", (f"Missing 'endsnippet' for {trig!r}", lines.line_index)

    if snip == "global":
        python_globals[trig].append(content)
    elif snip == "snippet":
        definition = UltiSnipsSnippetDefinition(
            priority,
            trig,
            content,
            descr,
            opts,
            python_globals,
            f"{filename}:{start_line_index}",
            context,
            pre_expand,
        )
        return "snippet", (definition,)
    else:
        return "error", (f"Invalid snippet type: '{snip}'", lines.line_index)


def _parse_snippets_file(data, filename):
    """Parse 'data' assuming it is a snippet file.

    Yields events in the file.

    """

    python_globals = defaultdict(list)
    lines = LineIterator(data)
    current_priority = 0
    actions = {}
    context = None
    for line in lines:
        if not line.strip():
            continue

        head, tail = head_tail(line)
        if head in ("snippet", "global"):
            snippet = _handle_snippet_or_global(
                filename,
                line,
                lines,
                python_globals,
                current_priority,
                actions,
                context,
            )

            actions = {}
            context = None
            if snippet is not None:
                yield snippet
        elif head == "extends":
            yield handle_extends(tail, lines.line_index)
        elif head == "clearsnippets":
            yield "clearsnippets", (current_priority, tail.split())
        elif head == "context":
            (
                head,
                context,
            ) = handle_context(tail, lines.line_index)
            if head == "error":
                yield (head, tail)
        elif head == "priority":
            try:
                current_priority = int(tail.split()[0])
            except (ValueError, IndexError):
                yield "error", (f"Invalid priority {tail!r}", lines.line_index)
        elif head in ["pre_expand", "post_expand", "post_jump"]:
            head, tail = handle_action(head, tail, lines.line_index)
            if head == "error":
                yield (head, tail)
            else:
                (actions[head],) = tail
        elif head and not head.startswith("#"):
            yield "error", (f"Invalid line {line.rstrip()!r}", lines.line_index)


class UltiSnipsFileSource(SnippetFileSource):
    """Manages all snippets definitions found in rtp for ultisnips."""

    def _get_all_snippet_files_for(self, ft):
        return find_all_snippet_files(ft)

    def _parse_snippet_file(self, filedata, filename):
        yield from _parse_snippets_file(filedata, filename)
