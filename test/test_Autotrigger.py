from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

import subprocess


def has_patch(version, executable):
    output = subprocess.check_output([executable, "--version"])
    for line in output.split("\n"):
        if line.startswith("Included patches:"):
            patch = line.split('-')[1]

    return int(patch) >= version


class Autotrigger_CanMatchSimpleTrigger(_VimTest):
    skip_if = lambda self: 'Vim newer than 7.4.214 is required' if \
        not has_patch(214, self.vim._vim_executable) \
        else None
    files = { 'us/all.snippets': r"""
        snippet a "desc" A
        autotriggered
        endsnippet
        """}
    keys = 'a'
    wanted = 'autotriggered'


class Autotrigger_CanMatchContext(_VimTest):
    skip_if = lambda self: 'Vim newer than 7.4.214 is required' if \
        not has_patch(214, self.vim._vim_executable) \
        else None
    files = { 'us/all.snippets': r"""
        snippet a "desc" "snip.line == 2" Ae
        autotriggered
        endsnippet
        """}
    keys = 'a\na'
    wanted = 'autotriggered\na'
