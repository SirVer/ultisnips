from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Completion_SimpleExample_ECR(_VimTest):
    snippets = ("test", "$1 ${1:blah}")
    keys = (
        "superkallifragilistik\ntest"
        + EX
        + "sup"
        + COMPL_KW
        + COMPL_ACCEPT
        + " some more"
    )
    wanted = (
        "superkallifragilistik\nsuperkallifragilistik some more "
        "superkallifragilistik some more"
    )


# We need >2 different words with identical starts to create the
# popup-menu:
COMPLETION_OPTIONS = "completion1\ncompletion2\n"


class Completion_ForwardsJumpWithoutCOMPL_ACCEPT(_VimTest):
    # completions should not be truncated when JF is activated without having
    # pressed COMPL_ACCEPT (Bug #598903)
    snippets = ("test", "$1 $2")
    keys = COMPLETION_OPTIONS + "test" + EX + "com" + COMPL_KW + JF + "foo"
    wanted = COMPLETION_OPTIONS + "completion1 foo"


class Completion_BackwardsJumpWithoutCOMPL_ACCEPT(_VimTest):
    # completions should not be truncated when JB is activated without having
    # pressed COMPL_ACCEPT (Bug #598903)
    snippets = ("test", "$1 $2")
    keys = COMPLETION_OPTIONS + "test" + EX + "foo" + JF + "com" + COMPL_KW + JB + "foo"
    wanted = COMPLETION_OPTIONS + "foo completion1"
