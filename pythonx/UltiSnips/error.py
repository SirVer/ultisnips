#!/usr/bin/env python
# encoding: utf-8


class PebkacError(RuntimeError):
    """An error that was caused by a misconfiguration or error in a snippet,
    i.e. caused by the user. Hence: "Problem exists between keyboard and
    chair".
    """

    pass
