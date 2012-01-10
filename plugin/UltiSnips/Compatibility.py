#!/usr/bin/env python
# encoding: utf-8

"""
This file contains compatibility code to stay compatible with
as many python versions as possible.
"""

import sys

__all__ = ['as_unicode', 'compatible_exec', 'CheapTotalOrdering']

if sys.version_info >= (3,0):
    from UltiSnips.Compatibility_py3 import *

    class CheapTotalOrdering:
        """Total ordering only appears in python 2.7. We try to stay compatible with
        python 2.5 for now, so we define our own"""

        def __lt__(self, other):
            return self.__cmp__(other) < 0

        def __le__(self, other):
            return self.__cmp__(other) <= 0

        def __gt__(self, other):
            return self.__cmp__(other) > 0

        def __ge__(self, other):
            return self.__cmp__(other) >= 0

    def as_unicode(s):
        if isinstance(s, bytes):
            return s.decode("utf-8")
        return s

    def make_suitable_for_vim(s):
        return s
else:
    from UltiSnips.Compatibility_py2 import *

    class CheapTotalOrdering(object):
        """Total ordering only appears in python 2.7. We try to stay compatible with
        python 2.5 for now, so we define our own"""

        def __lt__(self, other):
            return self.__cmp__(other) < 0

        def __le__(self, other):
            return self.__cmp__(other) <= 0

        def __gt__(self, other):
            return self.__cmp__(other) > 0

        def __ge__(self, other):
            return self.__cmp__(other) >= 0

    def as_unicode(s):
        if not isinstance(s, unicode):
            return s.decode("utf-8")
        return s

    def make_suitable_for_vim(s):
        if isinstance(s, list):
            return [ a.encode("utf-8") for a in s ]
        return s.encode("utf-8")

