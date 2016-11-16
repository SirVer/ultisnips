from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Simple isExpandables  {{{#


class _SimpleExpands(_VimTest):
    snippets = ('hallo', 'Hallo Welt!')


class SimpleExpand_ExpectCorrectResult(_SimpleExpands):
    keys = 'hallo' + ':<c-u>:call UltiSnips#isExpandable()<cr>' + ':let @a = g:UltiSnips#isExpandable<cr>' + 'cc' + ':0put a'
    wanted = '1'


# End: Simple Expands  #}}}
