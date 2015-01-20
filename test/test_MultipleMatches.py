from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Selecting Between Same Triggers  {{{#


class _MultipleMatches(_VimTest):
    snippets = (('test', 'Case1', 'This is Case 1'),
                ('test', 'Case2', 'This is Case 2'))


class Multiple_SimpleCaseSelectFirst_ECR(_MultipleMatches):
    keys = 'test' + EX + '1\n'
    wanted = 'Case1'


class Multiple_SimpleCaseSelectSecond_ECR(_MultipleMatches):
    keys = 'test' + EX + '2\n'
    wanted = 'Case2'


class Multiple_SimpleCaseSelectTooHigh_ESelectLast(_MultipleMatches):
    keys = 'test' + EX + '5\n'
    wanted = 'Case2'


class Multiple_SimpleCaseSelectZero_EEscape(_MultipleMatches):
    keys = 'test' + EX + '0\n' + 'hi'
    wanted = 'testhi'


class Multiple_SimpleCaseEscapeOut_ECR(_MultipleMatches):
    keys = 'test' + EX + ESC + 'hi'
    wanted = 'testhi'


class Multiple_ManySnippetsOneTrigger_ECR(_VimTest):
    # Snippet definition {{{#
    snippets = (
        ('test', 'Case1', 'This is Case 1'),
        ('test', 'Case2', 'This is Case 2'),
        ('test', 'Case3', 'This is Case 3'),
        ('test', 'Case4', 'This is Case 4'),
        ('test', 'Case5', 'This is Case 5'),
        ('test', 'Case6', 'This is Case 6'),
        ('test', 'Case7', 'This is Case 7'),
        ('test', 'Case8', 'This is Case 8'),
        ('test', 'Case9', 'This is Case 9'),
        ('test', 'Case10', 'This is Case 10'),
        ('test', 'Case11', 'This is Case 11'),
        ('test', 'Case12', 'This is Case 12'),
        ('test', 'Case13', 'This is Case 13'),
        ('test', 'Case14', 'This is Case 14'),
        ('test', 'Case15', 'This is Case 15'),
        ('test', 'Case16', 'This is Case 16'),
        ('test', 'Case17', 'This is Case 17'),
        ('test', 'Case18', 'This is Case 18'),
        ('test', 'Case19', 'This is Case 19'),
        ('test', 'Case20', 'This is Case 20'),
        ('test', 'Case21', 'This is Case 21'),
        ('test', 'Case22', 'This is Case 22'),
        ('test', 'Case23', 'This is Case 23'),
        ('test', 'Case24', 'This is Case 24'),
        ('test', 'Case25', 'This is Case 25'),
        ('test', 'Case26', 'This is Case 26'),
        ('test', 'Case27', 'This is Case 27'),
        ('test', 'Case28', 'This is Case 28'),
        ('test', 'Case29', 'This is Case 29'),
    )  # }}}
    keys = 'test' + EX + ' ' + ESC + ESC + 'ahi'
    wanted = 'testhi'
# End: Selecting Between Same Triggers  #}}}
