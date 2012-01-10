#!/usr/bin/env python
# encoding: utf-8

"""
This file contains compatibility code to stay compatible with
as many python versions as possible.
"""

import sys

__all__ = ['as_unicode']

if sys.version_info >= (3,0):
    def as_unicode(s):
        if isinstance(s, bytes):
            return s.decode("utf-8")
        return s
else:
    def as_unicode(s):
        if not isinstance(s, unicode):
            return s.decode("uft-8")
        return s
