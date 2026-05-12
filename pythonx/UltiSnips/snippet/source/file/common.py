#!/usr/bin/env python3

"""Common code for snipMate and UltiSnips snippet files."""

from pathlib import Path


def normalize_file_path(path: str) -> str:
    """Resolves the path to its canonical form."""
    return str(Path(path).resolve())


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
