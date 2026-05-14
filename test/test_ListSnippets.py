from test.constant import LS
from test.vim_test_case import VimTestCase as _VimTest


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


# GH #1036: In-word snippets should be listed even when preceded by
# non-word characters.
class ListAllAvailable_InWordWithPrefix_ExpectCorrectResult(_VimTest):
    snippets = (("exists", "exists('${1}')", "exists check", "i"),)
    keys = "!exists" + LS + "1\n"
    wanted = "!exists('')"


# Word-boundary snippets should be listed when a partial trigger sits
# after a non-word character, and selecting one must replace only the
# partial suffix - not the preceding non-word chunk.
class ListAllAvailable_WordOptionPartialAfterPunctuation_ExpectCorrectResult(_VimTest):
    snippets = (("foo", "FOO", "foo word-snippet", "w"),)
    keys = "x.fo" + LS + "1\n"
    wanted = "x.FOO"


# GH #1226: a number larger than the list length used to be clamped to
# the last item, silently picking a snippet the user didn't choose (and a
# negative answer from a mouse click above the menu could IndexError).
# Treat any out-of-range answer as a cancellation.
class ListAllAvailable_OutOfRangeAnswer_Cancels(_ListAllSnippets):
    keys = "hallo test" + LS + "99\n"
    wanted = "hallo test"
