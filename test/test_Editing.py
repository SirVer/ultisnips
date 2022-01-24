from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Undo_RemoveMultilineSnippet(_VimTest):
    snippets = ("test", "Hello\naaa ${1} bbb\nWorld")
    keys = "test" + EX + ESC + "u"
    wanted = "test"


class Undo_RemoveEditInTabstop(_VimTest):
    snippets = ("test", "$1 Hello\naaa ${1} bbb\nWorld")
    keys = "hello test" + EX + "upsi" + ESC + "hh" + "iabcdef" + ESC + "u"
    wanted = "hello upsi Hello\naaa upsi bbb\nWorld"


class Undo_RemoveWholeSnippet(_VimTest):
    snippets = ("test", "Hello\n${1:Hello}World")
    keys = "first line\n\n\n\n\n\nthird line" + ESC + "3k0itest" + EX + ESC + "u6j"
    wanted = "first line\n\n\ntest\n\n\nthird line"


class Undo_RemoveOneSnippetByTime(_VimTest):
    snippets = ("i", "if:\n\t$1")
    keys = "i" + EX + "i" + EX + ESC + "u"
    wanted = "if:\n\ti"


class Undo_RemoveOneSnippetByTime2(_VimTest):
    snippets = ("i", "if:\n\t$1")
    keys = "i" + EX + "i" + EX + ESC + "uu"
    wanted = "if:\n\t"


class Undo_ChangesInPlaceholder(_VimTest):
    snippets = ("i", "if $1:\n\t$2")
    keys = "i" + EX + "asd" + JF + ESC + "u"
    wanted = "if :\n\t"


class Undo_CompletelyUndoSnippet(_VimTest):
    snippets = ("i", "if $1:\n\t$2")
    # undo 'feh'
    # undo 'asd'
    # undo snippet expansion
    # undo entering of 'i'
    keys = "i" + EX + "asd" + JF + "feh" + ESC + "uuuu"
    wanted = ""


class JumpForward_DefSnippet(_VimTest):
    snippets = ("test", "${1}\n`!p snip.rv = '\\n'.join(t[1].split())`\n\n${0:pass}")
    keys = "test" + EX + "a b c" + JF + "shallnot"
    wanted = "a b c\na\nb\nc\n\nshallnot"


class DeleteSnippetInsertion0(_VimTest):
    snippets = ("test", "${1:hello} $1")
    keys = "test" + EX + ESC + "Vkx" + "i\nworld\n"
    wanted = "world"


class DeleteSnippetInsertion1(_VimTest):
    snippets = ("test", r"$1${1/(.*)/(?0::.)/}")
    keys = "test" + EX + ESC + "u"
    wanted = "test"


class DoNotCrashOnUndoAndJumpInNestedSnippet(_VimTest):
    snippets = ("test", r"if $1: $2")
    keys = "test" + EX + "a" + JF + "test" + EX + ESC + "u" + JF
    wanted = "if a: test"


# Test for bug #927844
class DeleteLastTwoLinesInSnippet(_VimTest):
    snippets = ("test", "$1hello\nnice\nworld")
    keys = "test" + EX + ESC + "j2dd"
    wanted = "hello"


class DeleteCurrentTabStop1_JumpBack(_VimTest):
    snippets = ("test", "${1:hi}\nend")
    keys = "test" + EX + ESC + "ddi" + JB
    wanted = "end"


class DeleteCurrentTabStop2_JumpBack(_VimTest):
    snippets = ("test", "${1:hi}\n${2:world}\nend")
    keys = "test" + EX + JF + ESC + "ddi" + JB + "hello"
    wanted = "hello\nend"


class DeleteCurrentTabStop3_JumpAround(_VimTest):
    snippets = ("test", "${1:hi}\n${2:world}\nend")
    keys = "test" + EX + JF + ESC + "ddkji" + JB + "hello" + JF + "world"
    wanted = "hello\nendworld"


# Test for Bug #774917


class Backspace_TabStop_Zero(_VimTest):
    snippets = ("test", "A${1:C} ${0:DDD}", "This is Case 1")
    keys = "test" + EX + "A" + JF + BS + "BBB"
    wanted = "AA BBB"


class Backspace_TabStop_NotZero(_VimTest):
    snippets = ("test", "A${1:C} ${2:DDD}", "This is Case 1")
    keys = "test" + EX + "A" + JF + BS + "BBB"
    wanted = "AA BBB"


class UpdateModifiedSnippetWithoutCursorMove1(_VimTest):
    snippets = ("test", "${1:one}(${2:xxx})${3:three}")
    keys = "test" + EX + "aaaaa" + JF + BS + JF + "3333"
    wanted = "aaaaa()3333"


class UpdateModifiedSnippetWithoutCursorMove2(_VimTest):
    snippets = (
        "test",
        """\
private function ${1:functionName}(${2:arguments}):${3:Void}
{
    ${VISUAL}$0
}""",
    )
    keys = "test" + EX + "a" + JF + BS + JF + "Int" + JF + "body"
    wanted = """\
private function a():Int
{
    body
}"""
