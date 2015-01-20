from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# ${VISUAL}  {{{#


class Visual_NoVisualSelection_Ignore(_VimTest):
    snippets = ('test', 'h${VISUAL}b')
    keys = 'test' + EX + 'abc'
    wanted = 'hbabc'


class Visual_SelectOneWord(_VimTest):
    snippets = ('test', 'h${VISUAL}b')
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX
    wanted = 'hblablubb'


class Visual_SelectOneWord_ProblemAfterTab(_VimTest):
    snippets = ('test', 'h${VISUAL}b', '', 'i')
    keys = '\tblablub' + ESC + '5hv3l' + EX + 'test' + EX
    wanted = '\tbhlablbub'


class VisualWithDefault_ExpandWithoutVisual(_VimTest):
    snippets = ('test', 'h${VISUAL:world}b')
    keys = 'test' + EX + 'hi'
    wanted = 'hworldbhi'


class VisualWithDefaultWithSlashes_ExpandWithoutVisual(_VimTest):
    snippets = ('test', r"h${VISUAL:\/\/ body}b")
    keys = 'test' + EX + 'hi'
    wanted = 'h// bodybhi'


class VisualWithDefault_ExpandWithVisual(_VimTest):
    snippets = ('test', 'h${VISUAL:world}b')
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX
    wanted = 'hblablubb'


class Visual_ExpandTwice(_VimTest):
    snippets = ('test', 'h${VISUAL}b')
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX + '\ntest' + EX
    wanted = 'hblablubb\nhb'


class Visual_SelectOneWord_TwiceVisual(_VimTest):
    snippets = ('test', 'h${VISUAL}b${VISUAL}a')
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX
    wanted = 'hblablubbblabluba'


class Visual_SelectOneWord_Inword(_VimTest):
    snippets = ('test', 'h${VISUAL}b', 'Description', 'i')
    keys = 'blablub' + ESC + '0lv4l' + EX + 'test' + EX
    wanted = 'bhlablubb'


class Visual_SelectOneWord_TillEndOfLine(_VimTest):
    snippets = ('test', 'h${VISUAL}b', 'Description', 'i')
    keys = 'blablub' + ESC + '0v$' + EX + 'test' + EX + ESC + 'o'
    wanted = 'hblablub\nb'


class Visual_SelectOneWordWithTabstop_TillEndOfLine(_VimTest):
    snippets = ('test', 'h${2:ahh}${VISUAL}${1:ups}b', 'Description', 'i')
    keys = 'blablub' + ESC + '0v$' + EX + 'test' + \
        EX + 'mmm' + JF + 'n' + JF + 'done' + ESC + 'o'
    wanted = 'hnblablub\nmmmbdone'


class Visual_InDefaultText_SelectOneWord_NoOverwrite(_VimTest):
    snippets = ('test', 'h${1:${VISUAL}}b')
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX + JF + 'hello'
    wanted = 'hblablubbhello'


class Visual_InDefaultText_SelectOneWord(_VimTest):
    snippets = ('test', 'h${1:${VISUAL}}b')
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX + 'hello'
    wanted = 'hhellob'


class Visual_CrossOneLine(_VimTest):
    snippets = ('test', 'h${VISUAL}b')
    keys = 'bla blub\n  helloi' + ESC + '0k4lvjll' + EX + 'test' + EX
    wanted = 'bla hblub\n  hellobi'


class Visual_LineSelect_Simple(_VimTest):
    snippets = ('test', 'h${VISUAL}b')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX
    wanted = 'hhello\n nice\n worldb'


class Visual_InDefaultText_LineSelect_NoOverwrite(_VimTest):
    snippets = ('test', 'h${1:bef${VISUAL}aft}b')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX + JF + 'hi'
    wanted = 'hbefhello\n    nice\n    worldaftbhi'


class Visual_InDefaultText_LineSelect_Overwrite(_VimTest):
    snippets = ('test', 'h${1:bef${VISUAL}aft}b')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + \
        EX + 'test' + EX + 'jup' + JF + 'hi'
    wanted = 'hjupbhi'


class Visual_LineSelect_CheckIndentSimple(_VimTest):
    snippets = ('test', 'beg\n\t${VISUAL}\nend')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX
    wanted = 'beg\n\thello\n\tnice\n\tworld\nend'


class Visual_LineSelect_CheckIndentTwice(_VimTest):
    snippets = ('test', 'beg\n\t${VISUAL}\nend')
    keys = '    hello\n    nice\n\tworld' + ESC + 'Vkk' + EX + 'test' + EX
    wanted = 'beg\n\t    hello\n\t    nice\n\t\tworld\nend'


class Visual_InDefaultText_IndentSpacesToTabstop_NoOverwrite(_VimTest):
    snippets = ('test', 'h${1:beforea${VISUAL}aft}b')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX + JF + 'hi'
    wanted = 'hbeforeahello\n\tnice\n\tworldaftbhi'


class Visual_InDefaultText_IndentSpacesToTabstop_Overwrite(_VimTest):
    snippets = ('test', 'h${1:beforea${VISUAL}aft}b')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + \
        EX + 'test' + EX + 'ups' + JF + 'hi'
    wanted = 'hupsbhi'


class Visual_InDefaultText_IndentSpacesToTabstop_NoOverwrite1(_VimTest):
    snippets = ('test', 'h${1:beforeaaa${VISUAL}aft}b')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX + JF + 'hi'
    wanted = 'hbeforeaaahello\n\t  nice\n\t  worldaftbhi'


class Visual_InDefaultText_IndentBeforeTabstop_NoOverwrite(_VimTest):
    snippets = ('test', 'hello\n\t ${1:${VISUAL}}\nend')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX + JF + 'hi'
    wanted = 'hello\n\t hello\n\t nice\n\t world\nendhi'


class Visual_LineSelect_WithTabStop(_VimTest):
    snippets = ('test', 'beg\n\t${VISUAL}\n\t${1:here_we_go}\nend')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + \
        EX + 'test' + EX + 'super' + JF + 'done'
    wanted = 'beg\n\thello\n\tnice\n\tworld\n\tsuper\nenddone'


class Visual_LineSelect_CheckIndentWithTS_NoOverwrite(_VimTest):
    snippets = ('test', 'beg\n\t${0:${VISUAL}}\nend')
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX
    wanted = 'beg\n\thello\n\tnice\n\tworld\nend'


class Visual_LineSelect_DedentLine(_VimTest):
    snippets = ('if', 'if {\n\t${VISUAL}$0\n}')
    keys = 'if' + EX + 'one\n\ttwo\n\tthree' + ESC + \
        ARR_U * 2 + 'V' + ARR_D + EX + '\tif' + EX
    wanted = 'if {\n\tif {\n\t\tone\n\t\ttwo\n\t}\n\tthree\n}'


class VisualTransformation_SelectOneWord(_VimTest):
    snippets = ('test', r"h${VISUAL/./\U$0\E/g}b")
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX
    wanted = 'hBLABLUBb'


class VisualTransformationWithDefault_ExpandWithoutVisual(_VimTest):
    snippets = ('test', r"h${VISUAL:world/./\U$0\E/g}b")
    keys = 'test' + EX + 'hi'
    wanted = 'hWORLDbhi'


class VisualTransformationWithDefault_ExpandWithVisual(_VimTest):
    snippets = ('test', r"h${VISUAL:world/./\U$0\E/g}b")
    keys = 'blablub' + ESC + '0v6l' + EX + 'test' + EX
    wanted = 'hBLABLUBb'


class VisualTransformation_LineSelect_Simple(_VimTest):
    snippets = ('test', r"h${VISUAL/./\U$0\E/g}b")
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX
    wanted = 'hHELLO\n NICE\n WORLDb'


class VisualTransformation_InDefaultText_LineSelect_NoOverwrite(_VimTest):
    snippets = ('test', r"h${1:bef${VISUAL/./\U$0\E/g}aft}b")
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + EX + 'test' + EX + JF + 'hi'
    wanted = 'hbefHELLO\n    NICE\n    WORLDaftbhi'


class VisualTransformation_InDefaultText_LineSelect_Overwrite(_VimTest):
    snippets = ('test', r"h${1:bef${VISUAL/./\U$0\E/g}aft}b")
    keys = 'hello\nnice\nworld' + ESC + 'Vkk' + \
        EX + 'test' + EX + 'jup' + JF + 'hi'
    wanted = 'hjupbhi'

# End: ${VISUAL}  #}}}
