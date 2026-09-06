#!/usr/bin/env python3

"""Common code for snipMate and UltiSnips snippet files."""

from pathlib import Path


def normalize_file_path(path: str) -> str:
    """Resolves the path to its canonical form."""
    return str(Path(path).resolve())


def expand_runtimepath_entry(pth: Path) -> list[Path]:
    """Expands the wildcards Vim allows in 'runtimepath' entries (see
    :help 'runtimepath') and returns the existing paths matching `pth`, a
    runtimepath entry joined with a snippet directory name.

    Only the tail of the path starting at its first wildcard component is
    globbed. Handing the whole path to `Path.glob` from the filesystem root
    made Python 3.12 list every directory on the way down, once per
    runtimepath entry: 3.12 dropped pathlib's fast path for literal pattern
    segments when it gained `case_sensitive` (python/cpython#102710) and
    3.13 brought it back (python/cpython#117732) without a backport. On slow
    filesystems that took seconds, and it silently found nothing when an
    ancestor directory was not listable (#1694).
    """
    parts = pth.parts
    for index, part in enumerate(parts):
        if any(char in part for char in "*?["):
            pattern = str(Path(*parts[index:]))
            return list(Path(*parts[:index]).glob(pattern))
    return [pth] if pth.exists() else []


def handle_extends(tail, line_index):
    """Handles an extends line in a snippet."""
    if tail:
        filetypes = []
        for p in tail.split(","):
            p = p.strip()
            # `extends` takes filetype names, not file names. Tolerate the
            # common mistake of including the .snippets extension.
            if p.endswith(".snippets"):
                p = p[: -len(".snippets")]
            filetypes.append(p)
        return "extends", (filetypes,)
    return "error", ("'extends' without file types", line_index)


def handle_action(head, tail, line_index):
    if tail:
        action = tail.strip('"').replace(r"\"", '"').replace(r"\\\\", r"\\")
        return head, (action,)
    return "error", (f"'{head}' without specified action", line_index)


def handle_context(tail, line_index):
    if tail:
        return "context", tail.strip('"').replace(r"\"", '"').replace(r"\\\\", r"\\")
    return "error", ("'context' without body", line_index)
