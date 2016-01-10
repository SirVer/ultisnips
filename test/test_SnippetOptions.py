# encoding: utf-8
from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *
from test.util import running_on_windows

# Snippet Options  {{{#


class SnippetOptions_OnlyExpandWhenWSInFront_Expand(_VimTest):
    snippets = ('test', 'Expand me!', '', 'b')
    keys = 'test' + EX
    wanted = 'Expand me!'


class SnippetOptions_OnlyExpandWhenWSInFront_Expand2(_VimTest):
    snippets = ('test', 'Expand me!', '', 'b')
    keys = '   test' + EX
    wanted = '   Expand me!'


class SnippetOptions_OnlyExpandWhenWSInFront_DontExpand(_VimTest):
    snippets = ('test', 'Expand me!', '', 'b')
    keys = 'a test' + EX
    wanted = 'a test' + EX


class SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWO(_VimTest):
    snippets = (
        ('test', 'Expand me!', '', 'b'),
        ('test', 'not at beginning', '', ''),
    )
    keys = 'a test' + EX
    wanted = 'a not at beginning'


class SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWOChoose(_VimTest):
    snippets = (
        ('test', 'Expand me!', '', 'b'),
        ('test', 'not at beginning', '', ''),
    )
    keys = '  test' + EX + '1\n'
    wanted = '  Expand me!'


class SnippetOptions_ExpandInwordSnippets_SimpleExpand(_VimTest):
    snippets = (('test', 'Expand me!', '', 'i'), )
    keys = 'atest' + EX
    wanted = 'aExpand me!'


class SnippetOptions_ExpandInwordSnippets_ExpandSingle(_VimTest):
    snippets = (('test', 'Expand me!', '', 'i'), )
    keys = 'test' + EX
    wanted = 'Expand me!'


class SnippetOptions_ExpandInwordSnippetsWithOtherChars_Expand(_VimTest):
    snippets = (('test', 'Expand me!', '', 'i'), )
    keys = '$test' + EX
    wanted = '$Expand me!'


class SnippetOptions_ExpandInwordSnippetsWithOtherChars_Expand2(_VimTest):
    snippets = (('test', 'Expand me!', '', 'i'), )
    keys = '-test' + EX
    wanted = '-Expand me!'


class SnippetOptions_ExpandInwordSnippetsWithOtherChars_Expand3(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = (('test', 'Expand me!', '', 'i'), )
    keys = 'ßßtest' + EX
    wanted = 'ßßExpand me!'


class _SnippetOptions_ExpandWordSnippets(_VimTest):
    snippets = (('test', 'Expand me!', '', 'w'), )


class SnippetOptions_ExpandWordSnippets_NormalExpand(
        _SnippetOptions_ExpandWordSnippets):
    keys = 'test' + EX
    wanted = 'Expand me!'


class SnippetOptions_ExpandWordSnippets_NoExpand(
        _SnippetOptions_ExpandWordSnippets):
    keys = 'atest' + EX
    wanted = 'atest' + EX


class SnippetOptions_ExpandWordSnippets_ExpandSuffix(
        _SnippetOptions_ExpandWordSnippets):
    keys = 'a-test' + EX
    wanted = 'a-Expand me!'


class SnippetOptions_ExpandWordSnippets_ExpandSuffix2(
        _SnippetOptions_ExpandWordSnippets):
    keys = 'a(test' + EX
    wanted = 'a(Expand me!'


class SnippetOptions_ExpandWordSnippets_ExpandSuffix3(
        _SnippetOptions_ExpandWordSnippets):
    keys = '[[test' + EX
    wanted = '[[Expand me!'


class _No_Tab_Expand(_VimTest):
    snippets = ('test', '\t\tExpand\tme!\t', '', 't')


class No_Tab_Expand_Simple(_No_Tab_Expand):
    keys = 'test' + EX
    wanted = '\t\tExpand\tme!\t'


class No_Tab_Expand_Leading_Spaces(_No_Tab_Expand):
    keys = '  test' + EX
    wanted = '  \t\tExpand\tme!\t'


class No_Tab_Expand_Leading_Tabs(_No_Tab_Expand):
    keys = '\ttest' + EX
    wanted = '\t\t\tExpand\tme!\t'


class No_Tab_Expand_No_TS(_No_Tab_Expand):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set sw=3')
        vim_config.append('set sts=3')
    keys = 'test' + EX
    wanted = '\t\tExpand\tme!\t'


class No_Tab_Expand_ET(_No_Tab_Expand):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set sw=3')
        vim_config.append('set expandtab')
    keys = 'test' + EX
    wanted = '\t\tExpand\tme!\t'


class No_Tab_Expand_ET_Leading_Spaces(_No_Tab_Expand):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set sw=3')
        vim_config.append('set expandtab')
    keys = '  test' + EX
    wanted = '  \t\tExpand\tme!\t'


class No_Tab_Expand_ET_SW(_No_Tab_Expand):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set sw=8')
        vim_config.append('set expandtab')
    keys = 'test' + EX
    wanted = '\t\tExpand\tme!\t'


class No_Tab_Expand_ET_SW_TS(_No_Tab_Expand):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set sw=3')
        vim_config.append('set sts=3')
        vim_config.append('set ts=3')
        vim_config.append('set expandtab')
    keys = 'test' + EX
    wanted = '\t\tExpand\tme!\t'


class _TabExpand_RealWorld(object):
    snippets = ('hi',
                r"""hi
`!p snip.rv="i1\n"
snip.rv += snip.mkline("i1\n")
snip.shift(1)
snip.rv += snip.mkline("i2\n")
snip.unshift(2)
snip.rv += snip.mkline("i0\n")
snip.shift(3)
snip.rv += snip.mkline("i3")`
snip.rv = repr(snip.rv)
End""")


class No_Tab_Expand_RealWorld(_TabExpand_RealWorld, _VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set noexpandtab')
    keys = '\t\thi' + EX
    wanted = """\t\thi
\t\ti1
\t\ti1
\t\t\ti2
\ti0
\t\t\t\ti3
\t\tsnip.rv = repr(snip.rv)
\t\tEnd"""


class SnippetOptions_Regex_Expand(_VimTest):
    snippets = ('(test)', 'Expand me!', '', 'r')
    keys = 'test' + EX
    wanted = 'Expand me!'


class SnippetOptions_Regex_WithSpace(_VimTest):
    snippets = ('test ', 'Expand me!', '', 'r')
    keys = 'test ' + EX
    wanted = 'Expand me!'


class SnippetOptions_Regex_Multiple(_VimTest):
    snippets = ('(test *)+', 'Expand me!', '', 'r')
    keys = 'test test test' + EX
    wanted = 'Expand me!'


class _Regex_Self(_VimTest):
    snippets = ('((?<=\W)|^)(\.)', 'self.', '', 'r')


class SnippetOptions_Regex_Self_Start(_Regex_Self):
    keys = '.' + EX
    wanted = 'self.'


class SnippetOptions_Regex_Self_Space(_Regex_Self):
    keys = ' .' + EX
    wanted = ' self.'


class SnippetOptions_Regex_Self_TextAfter(_Regex_Self):
    keys = ' .a' + EX
    wanted = ' .a' + EX


class SnippetOptions_Regex_Self_TextBefore(_Regex_Self):
    keys = 'a.' + EX
    wanted = 'a.' + EX


class SnippetOptions_Regex_PythonBlockMatch(_VimTest):
    snippets = (r"([abc]+)([def]+)", r"""`!p m = match
snip.rv += m.group(2)
snip.rv += m.group(1)
`""", '', 'r')
    keys = 'test cabfed' + EX
    wanted = 'test fedcab'


class SnippetOptions_Regex_PythonBlockNoMatch(_VimTest):
    snippets = (r"cabfed", r"""`!p snip.rv =  match or "No match"`""")
    keys = 'test cabfed' + EX
    wanted = 'test No match'
# Tests for Bug #691575


class SnippetOptions_Regex_SameLine_Long_End(_VimTest):
    snippets = ('(test.*)', 'Expand me!', '', 'r')
    keys = 'test test abc' + EX
    wanted = 'Expand me!'


class SnippetOptions_Regex_SameLine_Long_Start(_VimTest):
    snippets = ('(.*test)', 'Expand me!', '', 'r')
    keys = 'abc test test' + EX
    wanted = 'Expand me!'


class SnippetOptions_Regex_SameLine_Simple(_VimTest):
    snippets = ('(test)', 'Expand me!', '', 'r')
    keys = 'abc test test' + EX
    wanted = 'abc test Expand me!'


class MultiWordSnippet_Simple(_VimTest):
    snippets = ('test me', 'Expand me!')
    keys = 'test me' + EX
    wanted = 'Expand me!'


class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_Expand(_VimTest):
    snippets = ('test it', 'Expand me!', '', 'b')
    keys = 'test it' + EX
    wanted = 'Expand me!'


class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_Expand2(_VimTest):
    snippets = ('test it', 'Expand me!', '', 'b')
    keys = '   test it' + EX
    wanted = '   Expand me!'


class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_DontExpand(_VimTest):
    snippets = ('test it', 'Expand me!', '', 'b')
    keys = 'a test it' + EX
    wanted = 'a test it' + EX


class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWO(_VimTest):
    snippets = (
        ('test it', 'Expand me!', '', 'b'),
        ('test it', 'not at beginning', '', ''),
    )
    keys = 'a test it' + EX
    wanted = 'a not at beginning'


class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWOChoose(
        _VimTest):
    snippets = (
        ('test it', 'Expand me!', '', 'b'),
        ('test it', 'not at beginning', '', ''),
    )
    keys = '  test it' + EX + '1\n'
    wanted = '  Expand me!'


class MultiWord_SnippetOptions_ExpandInwordSnippets_SimpleExpand(_VimTest):
    snippets = (('test it', 'Expand me!', '', 'i'), )
    keys = 'atest it' + EX
    wanted = 'aExpand me!'


class MultiWord_SnippetOptions_ExpandInwordSnippets_ExpandSingle(_VimTest):
    snippets = (('test it', 'Expand me!', '', 'i'), )
    keys = 'test it' + EX
    wanted = 'Expand me!'


class _MultiWord_SnippetOptions_ExpandWordSnippets(_VimTest):
    snippets = (('test it', 'Expand me!', '', 'w'), )


class MultiWord_SnippetOptions_ExpandWordSnippets_NormalExpand(
        _MultiWord_SnippetOptions_ExpandWordSnippets):
    keys = 'test it' + EX
    wanted = 'Expand me!'


class MultiWord_SnippetOptions_ExpandWordSnippets_NoExpand(
        _MultiWord_SnippetOptions_ExpandWordSnippets):
    keys = 'atest it' + EX
    wanted = 'atest it' + EX


class MultiWord_SnippetOptions_ExpandWordSnippets_ExpandSuffix(
        _MultiWord_SnippetOptions_ExpandWordSnippets):
    keys = 'a-test it' + EX
    wanted = 'a-Expand me!'
# Snippet Options  #}}}
