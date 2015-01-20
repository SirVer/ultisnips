from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# List Snippets  {{{#


class _ListAllSnippets(_VimTest):
    snippets = (('testblah', 'BLAAH', 'Say BLAH'),
                ('test', 'TEST ONE', 'Say tst one'),
                ('aloha', 'OHEEEE', 'Say OHEE'),
                )


class ListAllAvailable_NothingTyped_ExpectCorrectResult(_ListAllSnippets):
    keys = '' + LS + '3\n'
    wanted = 'BLAAH'


class ListAllAvailable_SpaceInFront_ExpectCorrectResult(_ListAllSnippets):
    keys = ' ' + LS + '3\n'
    wanted = ' BLAAH'


class ListAllAvailable_BraceInFront_ExpectCorrectResult(_ListAllSnippets):
    keys = '} ' + LS + '3\n'
    wanted = '} BLAAH'


class ListAllAvailable_testtyped_ExpectCorrectResult(_ListAllSnippets):
    keys = 'hallo test' + LS + '2\n'
    wanted = 'hallo BLAAH'


class ListAllAvailable_testtypedSecondOpt_ExpectCorrectResult(
        _ListAllSnippets):
    keys = 'hallo test' + LS + '1\n'
    wanted = 'hallo TEST ONE'


class ListAllAvailable_NonDefined_NoExpectionShouldBeRaised(_ListAllSnippets):
    keys = 'hallo qualle' + LS + 'Hi'
    wanted = 'hallo qualleHi'
# End: List Snippets  #}}}
