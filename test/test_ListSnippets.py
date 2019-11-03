from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class _ListAllSnippets(_VimTest):
    snippets = (
        ("testblah", "BLAAH", "Say BLAH"),
        ("test", "TEST ONE", "Say tst one"),
        ("aloha", "OHEEEE", "Say OHEE"),
    )


class ListAllAvailable_NothingTyped_ExpectCorrectResult(_ListAllSnippets):
    keys = "" + LS + "3\n"
    wanted = "BLAAH"


class ListAllAvailable_SpaceInFront_ExpectCorrectResult(_ListAllSnippets):
    keys = " " + LS + "3\n"
    wanted = " BLAAH"


class ListAllAvailable_BraceInFront_ExpectCorrectResult(_ListAllSnippets):
    keys = "} " + LS + "3\n"
    wanted = "} BLAAH"


class ListAllAvailable_testtyped_ExpectCorrectResult(_ListAllSnippets):
    keys = "hallo test" + LS + "2\n"
    wanted = "hallo BLAAH"


class ListAllAvailable_testtypedSecondOpt_ExpectCorrectResult(_ListAllSnippets):
    keys = "hallo test" + LS + "1\n"
    wanted = "hallo TEST ONE"


class ListAllAvailable_NonDefined_NoExpectionShouldBeRaised(_ListAllSnippets):
    keys = "hallo qualle" + LS + "Hi"
    wanted = "hallo qualleHi"


class ListAllAvailable_Disabled_ExpectCorrectResult(_ListAllSnippets):
    keys = "hallo test" + LS + "2\n"
    wanted = "hallo test" + LS + "2\n"

    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UltiSnipsListSnippets=""')
