from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class _SimpleExpands(_VimTest):
    snippets = ("hallo", "Hallo Welt!")


class SimpleExpand_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX
    wanted = "Hallo Welt!"


class SimpleExpandTwice_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + "\nhallo" + EX
    wanted = "Hallo Welt!\nHallo Welt!"


class SimpleExpandNewLineAndBackspae_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + "\nHallo Welt!\n\n\b\b\b\b\b"
    wanted = "Hallo Welt!\nHallo We"

    def _extra_vim_config(self, vim_config):
        vim_config.append("set backspace=eol,start")


class SimpleExpandTypeAfterExpand_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + "and again"
    wanted = "Hallo Welt!and again"


class SimpleExpandTypeAndDelete_ExpectCorrectResult(_SimpleExpands):
    keys = "na du hallo" + EX + "and again\b\b\b\b\bblub"
    wanted = "na du Hallo Welt!and blub"


class DoNotExpandAfterSpace_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo " + EX
    wanted = "hallo " + EX


class ExitSnippetModeAfterTabstopZero(_VimTest):
    snippets = ("test", "SimpleText")
    keys = "test" + EX + EX
    wanted = "SimpleText" + EX


class ExpandInTheMiddleOfLine_ExpectCorrectResult(_SimpleExpands):
    keys = "Wie hallo gehts" + ESC + "bhi" + EX
    wanted = "Wie Hallo Welt! gehts"


class MultilineExpand_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts")
    keys = "Wie hallo gehts" + ESC + "bhi" + EX
    wanted = "Wie Hallo Welt!\nUnd Wie gehts gehts"


class MultilineExpandTestTyping_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts")
    wanted = "Wie Hallo Welt!\nUnd Wie gehtsHuiui! gehts"
    keys = "Wie hallo gehts" + ESC + "bhi" + EX + "Huiui!"


class SimpleExpandEndingWithNewline_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt\n")
    keys = "hallo" + EX + "\nAnd more"
    wanted = "Hallo Welt\n\nAnd more"


class SimpleExpand_DoNotClobberDefaultRegister(_VimTest):
    snippets = ("hallo", "Hallo ${1:Welt}")
    keys = "hallo" + EX + BS + ESC + "o" + ESC + "P"
    wanted = "Hallo \n"

    def _extra_vim_config(self, vim_config):
        vim_config.append('let @"=""')


class SimpleExpand_Issue1343(_VimTest):
    snippets = ("test", r"${1:\Safe\\}")
    keys = "test" + EX + JF + "foo"
    wanted = r"\Safe\foo"
