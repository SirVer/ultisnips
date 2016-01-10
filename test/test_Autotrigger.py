from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

def check_required_vim_version(test):
    if test.vim_flavor == 'neovim':
        return None
    if not test.vim.has_patch(214):
        return 'Vim newer than 7.4.214 is required'
    else:
        return None


class Autotrigger_CanMatchSimpleTrigger(_VimTest):
    skip_if = check_required_vim_version
    files = { 'us/all.snippets': r"""
        snippet a "desc" A
        autotriggered
        endsnippet
        """}
    keys = 'a'
    wanted = 'autotriggered'


class Autotrigger_CanMatchContext(_VimTest):
    skip_if = check_required_vim_version
    files = { 'us/all.snippets': r"""
        snippet a "desc" "snip.line == 2" Ae
        autotriggered
        endsnippet
        """}
    keys = 'a\na'
    wanted = 'autotriggered\na'


class Autotrigger_CanExpandOnTriggerWithLengthMoreThanOne(_VimTest):
    skip_if = check_required_vim_version
    files = { 'us/all.snippets': r"""
        snippet abc "desc" A
        autotriggered
        endsnippet
        """}
    keys = 'abc'
    wanted = 'autotriggered'


class Autotrigger_WillProduceNoExceptionWithVimLowerThan214(_VimTest):
    skip_if = lambda self: 'Vim older than 7.4.214 is required' \
        if self.vim.has_patch(214) else None

    files = { 'us/all.snippets': r"""
        snippet abc "desc" A
        autotriggered
        endsnippet
        """}
    keys = 'abc'
    wanted = 'abc'
