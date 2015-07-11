from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *
from test.util import running_on_windows

# ExpandTab  {{{#


class _ExpandTabs(_VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set sw=3')
        vim_config.append('set expandtab')


class RecTabStopsWithExpandtab_SimpleExample_ECR(_ExpandTabs):
    snippets = ('m', '\tBlaahblah \t\t  ')
    keys = 'm' + EX
    wanted = '   Blaahblah \t\t  '


class RecTabStopsWithExpandtab_SpecialIndentProblem_ECR(_ExpandTabs):
    # Windows indents the Something line after pressing return, though it
    # shouldn't because it contains a manual indent. All other vim versions do
    # not do this. Windows vim does not interpret the changes made by :py as
    # changes made 'manually', while the other vim version seem to do so. Since
    # the fault is not with UltiSnips, we simply skip this test on windows
    # completely.
    skip_if = lambda self: running_on_windows()
    snippets = (
        ('m1', 'Something'),
        ('m', '\t$0'),
    )
    keys = 'm' + EX + 'm1' + EX + '\nHallo'
    wanted = '   Something\n        Hallo'

    def _extra_vim_config(self, vim_config):
        _ExpandTabs._extra_vim_config(self, vim_config)
        vim_config.append('set indentkeys=o,O,*<Return>,<>>,{,}')
        vim_config.append('set indentexpr=8')
# End: ExpandTab  #}}}

# Proper Indenting  {{{#


class ProperIndenting_SimpleCase_ECR(_VimTest):
    snippets = ('test', 'for\n    blah')
    keys = '    test' + EX + 'Hui'
    wanted = '    for\n        blahHui'


class ProperIndenting_SingleLineNoReindenting_ECR(_VimTest):
    snippets = ('test', 'hui')
    keys = '    test' + EX + 'blah'
    wanted = '    huiblah'


class ProperIndenting_AutoIndentAndNewline_ECR(_VimTest):
    snippets = ('test', 'hui')
    keys = '    test' + EX + '\n' + 'blah'
    wanted = '    hui\n    blah'

    def _extra_vim_config(self, vim_config):
        vim_config.append('set autoindent')
# Test for bug 1073816


class ProperIndenting_FirstLineInFile_ECR(_VimTest):
    text_before = ''
    text_after = ''
    files = { 'us/all.snippets': r"""
global !p
def complete(t, opts):
  if t:
    opts = [ m[len(t):] for m in opts if m.startswith(t) ]
  if len(opts) == 1:
    return opts[0]
  elif len(opts) > 1:
    return "(" + "|".join(opts) + ")"
  else:
    return ""
endglobal

snippet '^#?inc' "#include <>" !r
#include <$1`!p snip.rv = complete(t[1], ['cassert', 'cstdio', 'cstdlib', 'cstring', 'fstream', 'iostream', 'sstream'])`>
endsnippet
        """}
    keys = 'inc' + EX + 'foo'
    wanted = '#include <foo>'


class ProperIndenting_FirstLineInFileComplete_ECR(
        ProperIndenting_FirstLineInFile_ECR):
    keys = 'inc' + EX + 'cstdl'
    wanted = '#include <cstdlib>'
# End: Proper Indenting  #}}}

# Format options tests  {{{#


class _FormatoptionsBase(_VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set tw=20')
        vim_config.append('set fo=lrqntc')


class FOSimple_Break_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ('test', '${1:longer expand}\n$1\n$0', '', 'f')
    keys = 'test' + EX + \
        'This is a longer text that should wrap as formatoptions are  enabled' + \
        JF + 'end'
    wanted = 'This is a longer\ntext that should\nwrap as\nformatoptions are\nenabled\n' + \
        'This is a longer\ntext that should\nwrap as\nformatoptions are\nenabled\n' + \
        'end'


class FOTextBeforeAndAfter_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ('test', 'Before${1:longer expand}After\nstart$1end')
    keys = 'test' + EX + 'This is a longer text that should wrap'
    wanted = \
        """BeforeThis is a
longer text that
should wrapAfter
startThis is a
longer text that
should wrapend"""


# Tests for https://bugs.launchpad.net/bugs/719998
class FOTextAfter_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ('test', '${1:longer expand}after\nstart$1end')
    keys = ('test' + EX + 'This is a longer snippet that should wrap properly '
            'and the mirror below should work as well')
    wanted = \
        """This is a longer
snippet that should
wrap properly and
the mirror below
should work as wellafter
startThis is a longer
snippet that should
wrap properly and
the mirror below
should work as wellend"""


class FOWrapOnLongWord_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ('test', '${1:longer expand}after\nstart$1end')
    keys = ('test' + EX + 'This is a longersnippet that should wrap properly')
    wanted = \
        """This is a
longersnippet that
should wrap properlyafter
startThis is a
longersnippet that
should wrap properlyend"""
# End: Format options tests  #}}}
