from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Undo of Snippet insertion  {{{#
class Undo_RemoveMultilineSnippet(_VimTest):
    snippets = ("test", "Hello\naaa ${1} bbb\nWorld")
    keys = "test" + EX + ESC + "u" + "inothing"
    wanted = "nothing"
class Undo_RemoveEditInTabstop(_VimTest):
    snippets = ("test", "$1 Hello\naaa ${1} bbb\nWorld")
    keys = "hello test" + EX + "upsi" + ESC + "hh" + "iabcdef" + ESC + "u"
    wanted = "hello upsi Hello\naaa upsi bbb\nWorld"
class Undo_RemoveWholeSnippet(_VimTest):
    snippets = ("test", "Hello\n${1:Hello}World")
    keys = "first line\n\n\n\n\n\nthird line" + \
            ESC + "3k0itest" + EX + ESC + "uiupsy"
    wanted = "first line\n\n\nupsy\n\n\nthird line"
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
    keys = "test" + EX + ESC + "u" + "i" + JF + "\t"
    wanted = "\t"
# End: Undo of Snippet insertion  #}}}

# Normal mode editing  {{{#
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

# End: Normal mode editing  #}}}

# Pressing BS in TabStop  {{{#
# Test for Bug #774917
class Backspace_TabStop_Zero(_VimTest):
    snippets = ("test", "A${1:C} ${0:DDD}", "This is Case 1")
    keys = "test" + EX + "A" + JF + BS + "BBB"
    wanted = "AA BBB"

class Backspace_TabStop_NotZero(_VimTest):
    snippets = ("test", "A${1:C} ${2:DDD}", "This is Case 1")
    keys = "test" + EX + "A" + JF + BS + "BBB"
    wanted = "AA BBB"
# End: Pressing BS in TabStop  #}}}
