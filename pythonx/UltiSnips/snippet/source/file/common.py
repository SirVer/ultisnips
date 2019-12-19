#!/usr/bin/env python
# encoding: utf-8

"""Common code for snipMate and UltiSnips snippet files."""

import os.path


def normalize_file_path(path: str) -> str:
    """Calls normpath and normcase on path"""
    return os.path.normcase(os.path.normpath(path))


def handle_extends(tail, line_index):
    """Handles an extends line in a snippet."""
    if tail:
        return "extends", ([p.strip() for p in tail.split(",")],)
    else:
        return "error", ("'extends' without file types", line_index)


def handle_action(head, tail, line_index):
    if tail:
        action = tail.strip('"').replace(r"\"", '"').replace(r"\\\\", r"\\")
        return head, (action,)
    else:
        return "error", ("'{}' without specified action".format(head), line_index)


def handle_context(tail, line_index):
    if tail:
        return "context", tail.strip('"').replace(r"\"", '"').replace(r"\\\\", r"\\")
    else:
        return "error", ("'context' without body", line_index)
