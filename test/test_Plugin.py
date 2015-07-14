import sys

from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

PYTHON3 = sys.version_info >= (3, 0)


def python3():
    if PYTHON3:
        return 'Test does not work on python3.'

# Plugin: YouCompleteMe  {{{#
# TODO(sirver): disabled because it fails right now.
# class Plugin_YouCompleteMe_IntegrationTest(_VimTest):
    # def skip_if(self):
        # r = python3()
        # if r:
        # return r
        # if "7.4" not in self.version:
        # return "Needs Vim 7.4."
    # plugins = ["Valloric/YouCompleteMe"]
    # snippets = ("superlongtrigger", "Hello")
    # keys = "superlo\ty"
    # wanted = "Hello"

    # def _extra_vim_config(self, vim_config):
        # # Not sure why, but I need to make a new tab for this to work.
        # vim_config.append('let g:UltiSnipsExpandTrigger="y"')
        # vim_config.append('tabnew')

    # def _before_test(self):
        # self.vim.send(":set ft=python\n")
        # # Give ycm a chance to catch up.
        # time.sleep(1)
# End: Plugin: YouCompleteMe  #}}}
# Plugin: Neocomplete {{{#
# TODO(sirver): disabled because it fails right now.
# class Plugin_Neocomplete_BugTest(_VimTest):
    # Test for https://github.com/SirVer/ultisnips/issues/228

    # def skip_if(self):
        # if '+lua' not in self.version:
            # return 'Needs +lua'
    # plugins = ['Shougo/neocomplete.vim']
    # snippets = ('t', 'Hello', '', 'w')
    # keys = 'iab\\ t' + EX
    # wanted = 'iab\\ Hello'

    # def _extra_vim_config(self, vim_config):
        # vim_config.append(r'set iskeyword+=\\ ')
        # vim_config.append('let g:neocomplete#enable_at_startup = 1')
        # vim_config.append('let g:neocomplete#enable_smart_case = 1')
        # vim_config.append('let g:neocomplete#enable_camel_case = 1')
        # vim_config.append('let g:neocomplete#enable_auto_delimiter = 1')
        # vim_config.append('let g:neocomplete#enable_refresh_always = 1')
# End: Plugin: Neocomplete  #}}}
# Plugin: unite {{{#

# TODO(sirver): Disable since it is flaky.
# class Plugin_unite_BugTest(_VimTest):
    # plugins = ['Shougo/unite.vim']
    # snippets = ('t', 'Hello', '', 'w')
    # keys = 'iab\\ t=UltiSnipsCallUnite()\n'
    # wanted = 'iab\\ Hello '

    # def _extra_vim_config(self, vim_config):
        # vim_config.append(r'set iskeyword+=\\ ')
        # vim_config.append('function! UltiSnipsCallUnite()')
        # vim_config.append(
            # '  Unite -start-insert -winheight=100 -immediately -no-empty ultisnips')
        # vim_config.append('  return ""')
        # vim_config.append('endfunction')
# End: Plugin: unite  #}}}
# Plugin: Supertab {{{#


class Plugin_SuperTab_SimpleTest(_VimTest):
    plugins = ['ervandew/supertab']
    snippets = ('long', 'Hello', '', 'w')
    keys = ('longtextlongtext\n' +
            'longt' + EX + '\n' +  # Should complete word
            'long' + EX)  # Should expand
    wanted = 'longtextlongtext\nlongtextlongtext\nHello'

    def _before_test(self):
        # Make sure that UltiSnips has the keymap
        self.vim.send_to_vim(':call UltiSnips#map_keys#MapKeys()\n')

    def _extra_vim_config(self, vim_config):
        assert EX == '\t'  # Otherwise this test needs changing.
        vim_config.append('let g:SuperTabDefaultCompletionType = "<c-p>"')
        vim_config.append('let g:SuperTabRetainCompletionDuration = "insert"')
        vim_config.append('let g:SuperTabLongestHighlight = 1')
        vim_config.append('let g:SuperTabCrMapping = 0')
# End: Plugin: Supertab   #}}}
