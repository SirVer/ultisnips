#!/usr/bin/env python
# encoding: utf-8

"""Common code for snipMate and UltiSnips snippet files."""

def handle_extends(tail, line_index):
    """Handles an extends line in a snippet."""
    if tail:
        return "extends", ([p.strip() for p in tail.split(',')],)
    else:
        return "error", ("'extends' without file types", line_index)
