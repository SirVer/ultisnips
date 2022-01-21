from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Autotrigger_CanMatchSimpleTrigger(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet a "desc" A
        autotriggered
        endsnippet
        """
    }
    keys = "a"
    wanted = "autotriggered"


class Autotrigger_CanMatchContext(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet a "desc" "snip.line == 2" Ae
        autotriggered
        endsnippet
        """
    }
    keys = "a\na"
    wanted = "autotriggered\na"


class Autotrigger_CanExpandOnTriggerWithLengthMoreThanOne(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet abc "desc" A
        autotriggered
        endsnippet
        """
    }
    keys = "abc"
    wanted = "autotriggered"


class Autotrigger_CanMatchPreviouslySelectedPlaceholder(_VimTest):

    files = {
        "us/all.snippets": r"""
        snippet if "desc"
        if ${1:var}: pass
        endsnippet
        snippet = "desc" "snip.last_placeholder" Ae
        `!p snip.rv = snip.context.current_text` == nil
        endsnippet
        """
    }
    keys = "if" + EX + "=" + ESC + "o="
    wanted = "if var == nil: pass\n="
