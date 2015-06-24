from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Autotrigger_CanMatchSimpleTrigger(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet a "desc" A
        autotriggered
        endsnippet
        """}
    keys = 'a'
    wanted = 'autotriggered'


class Autotrigger_CanMatchContext(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet a "desc" "snip.line == 2" Ae
        autotriggered
        endsnippet
        """}
    keys = 'a\na'
    wanted = 'autotriggered\na'
