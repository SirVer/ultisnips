from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Cursor Movement  {{{#


class CursorMovement_Multiline_ECR(_VimTest):
    snippets = ('test', r"$1 ${1:a tab}")
    keys = 'test' + EX + 'this is something\nvery nice\nnot' + JF + 'more text'
    wanted = 'this is something\nvery nice\nnot ' \
        'this is something\nvery nice\nnotmore text'


class CursorMovement_BS_InEditMode(_VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set backspace=eol,indent,start')
    snippets = ('<trh', '<tr>\n\t<th>$1</th>\n\t$2\n</tr>\n$3')
    keys = '<trh' + EX + 'blah' + JF + BS + BS + JF + 'end'
    wanted = '<tr>\n\t<th>blah</th>\n</tr>\nend'
# End: Cursor Movement  #}}}
# Insert Mode Moving  {{{#


class IMMoving_CursorsKeys_ECR(_VimTest):
    snippets = ('test', '${1:Some}')
    keys = 'test' + EX + 'text' + 3 * ARR_U + 6 * ARR_D
    wanted = 'text'


class IMMoving_AcceptInputWhenMoved_ECR(_VimTest):
    snippets = ('test', r"$1 ${1:a tab}")
    keys = 'test' + EX + 'this' + 2 * ARR_L + 'hallo\nwelt'
    wanted = 'thhallo\nweltis thhallo\nweltis'


class IMMoving_NoExiting_ECR(_VimTest):
    snippets = ('test', r"$1 ${2:a tab} ${1:Tab}")
    keys = 'hello test this' + ESC + '02f i' + EX + 'tab' + 7 * ARR_L + \
        JF + 'hallo'
    wanted = 'hello tab hallo tab this'


class IMMoving_NoExitingEventAtEnd_ECR(_VimTest):
    snippets = ('test', r"$1 ${2:a tab} ${1:Tab}")
    keys = 'hello test this' + ESC + '02f i' + EX + 'tab' + JF + 'hallo'
    wanted = 'hello tab hallo tab this'


class IMMoving_ExitWhenOutsideRight_ECR(_VimTest):
    snippets = ('test', r"$1 ${2:blub} ${1:Tab}")
    keys = 'hello test this' + ESC + '02f i' + \
        EX + 'tab' + ARR_R + JF + 'hallo'
    wanted = 'hello tab blub tab ' + JF + 'hallothis'


class IMMoving_NotExitingWhenBarelyOutsideLeft_ECR(_VimTest):
    snippets = ('test', r"${1:Hi} ${2:blub}")
    keys = 'hello test this' + ESC + '02f i' + EX + 'tab' + 3 * ARR_L + \
        JF + 'hallo'
    wanted = 'hello tab hallo this'


class IMMoving_ExitWhenOutsideLeft_ECR(_VimTest):
    snippets = ('test', r"${1:Hi} ${2:blub}")
    keys = 'hello test this' + ESC + '02f i' + EX + 'tab' + 4 * ARR_L + \
        JF + 'hallo'
    wanted = 'hello' + JF + 'hallo tab blub this'


class IMMoving_ExitWhenOutsideAbove_ECR(_VimTest):
    snippets = ('test', '${1:Hi}\n${2:blub}')
    keys = 'hello test this' + ESC + '02f i' + EX + 'tab' + 1 * ARR_U + '\n' + JF + \
        'hallo'
    wanted = JF + 'hallo\nhello tab\nblub this'


class IMMoving_ExitWhenOutsideBelow_ECR(_VimTest):
    snippets = ('test', '${1:Hi}\n${2:blub}')
    keys = 'hello test this' + ESC + '02f i' + EX + 'tab' + 2 * ARR_D + JF + \
        'testhallo\n'
    wanted = 'hello tab\nblub this\n' + JF + 'testhallo'
# End: Insert Mode Moving  #}}}
