import sys

from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Plugin_SuperTab_SimpleTest(_VimTest):
    plugins = ["ervandew/supertab"]
    snippets = ("long", "Hello", "", "w")
    keys = (
        "longtextlongtext\n" + "longt" + EX + "\n" + "long" + EX  # Should complete word
    )  # Should expand
    wanted = "longtextlongtext\nlongtextlongtext\nHello"

    def _before_test(self):
        # Make sure that UltiSnips has the keymap
        self.vim.send_to_vim(":call UltiSnips#map_keys#MapKeys()\n")

    def _extra_vim_config(self, vim_config):
        assert EX == "\t"  # Otherwise this test needs changing.
        vim_config.append('let g:SuperTabDefaultCompletionType = "<c-p>"')
        vim_config.append('let g:SuperTabRetainCompletionDuration = "insert"')
        vim_config.append("let g:SuperTabLongestHighlight = 1")
        vim_config.append("let g:SuperTabCrMapping = 0")


class Plugin_VimTemplate_SimpleTest(_VimTest):
    test_plugins = False
    plugins = ["srydell/vim-template"]
    snippets = ("_skel", "Hello", "", "b")
    keys = ()
    # NOTE: Trailing 'i' since the test suite
    #       expects to have to start insert mode
    wanted = "Helloi"


class Plugin_VimTemplate_JumpsTest(_VimTest):
    test_plugins = False
    plugins = ["srydell/vim-template"]
    snippets = ("_skel", "[ ${1:foo} ] ${2:bar}")
    keys = (
        "HelloWorld" + JF + JF
    )  # Should replace 'foo' with 'HelloWorld' but keep 'bar'

    # NOTE: Leading 'i' since the test suite
    #       expects to have to start insert mode
    wanted = "[ iHelloWorld ] bar"
