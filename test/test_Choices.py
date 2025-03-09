from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Choices_WillBeExpandedToInlineSelection(_VimTest):
    snippets = ("test", "${1|red,gray|}")
    keys = "test" + EX
    wanted = "1.red|2.gray"


class Choices_ExpectCorrectResult(_VimTest):
    snippets = ("test", "${1|red,gray|}")
    keys = "test" + EX + "2"
    wanted = "gray"


class Choices_WillAbandonSelection_If_CharTyped(_VimTest):
    snippets = ("test", "${1|red,green|}")
    keys = "test" + EX + "char"
    wanted = "char"


class Choices_WillAbandonSelection_If_InputIsGreaterThanMaxSelectionIndex(_VimTest):
    snippets = ("test", "${1|red,green|}")
    keys = "test" + EX + "3"
    wanted = "3"


class Choices_WilNotMessWithTabstopsAfterIt(_VimTest):
    snippets = ("test", "${1|red,gray|} is ${2:color}\nline 2")
    keys = "test" + EX + "2"
    wanted = "gray is color\nline 2"


class Choices_MoreThan9Candidates_ShouldWaitForInputs(_VimTest):
    snippets = ("test", "${1|a,b,c,d,e,f,g,h,i,j,k,l,m,n|} is ${2:a char}")
    keys = "test" + EX + "1"
    wanted = "1 is a char"


class Choices_MoreThan9Candidates_ShouldTerminateWithSpace(_VimTest):
    snippets = ("test", "${1|a,b,c,d,e,f,g,h,i,j,k,l,m,n|} is ${2:a char}")
    keys = "test" + EX + "1 "
    wanted = "a is a char"


class Choices_EmptyChoiceWillBeDiscarded(_VimTest):
    snippets = ("test", "${1|a,,c|}")
    keys = "test" + EX
    wanted = "1.a|2.c"


class Choices_WillNotExpand_If_ChoiceListIsEmpty(_VimTest):
    snippets = ("test", "${1||}")
    keys = "test" + EX
    wanted = "||"


class Choices_CanTakeNonAsciiCharacters(_VimTest):
    snippets = ("test", "${1|Русский язык,中文,한국어,öääö|}")
    keys = "test" + EX
    wanted = "1.Русский язык|2.中文|3.한국어|4.öääö"


class Choices_AsNestedElement_ShouldOverwriteDefaultText(_VimTest):
    snippets = ("test", "${1:outer ${2|foo,blah|}}")
    keys = "test" + EX
    wanted = "outer 1.foo|2.blah"


class Choices_AsNestedElement_ShallNotTakeActionIfParentInput(_VimTest):
    snippets = ("test", "${1:outer ${2|foo,blah|}}")
    keys = "test" + EX + "input"
    wanted = "input"


class Choices_AsNestedElement_CanBeTabbedInto(_VimTest):
    snippets = ("test", "${1:outer ${2|foo,blah|}}")
    keys = "test" + EX + JF + "1"
    wanted = "outer foo"


class Choices_AsNestedElement_CanBeTabbedThrough(_VimTest):
    snippets = ("test", "${1:outer ${2|foo,blah|}} ${3}")
    keys = "test" + EX + JF + JF + "input"
    wanted = "outer 1.foo|2.blah input"


class Choices_With_Mirror(_VimTest):
    snippets = ("test", "${1|cyan,magenta|}, mirror: $1")
    keys = "test" + EX + "1"
    wanted = "cyan, mirror: cyan"


class Choices_With_Mirror_ContinueMirroring_EvenAfterSelectionDone(_VimTest):
    snippets = ("test", "${1|cyan,magenta|}, mirror: $1")
    keys = "test" + EX + "1 is a color"
    wanted = "cyan is a color, mirror: cyan is a color"


class Choices_ShouldThrowErrorWithZeroTabstop(_VimTest):
    snippets = ("test", "${0|red,blue|}")
    keys = "test" + EX
    expected_error = r"Choices selection is not supported on \$0"


class Choices_CanEscapeCommaInsideChoiceItem(_VimTest):
    snippets = (
        "test",
        r"${1|fun1(,fun2(param1\, ,fun3(param1\, param2\, |}param_end) result: $1",
    )
    keys = "test" + EX + "2"
    wanted = "fun2(param1, param_end) result: fun2(param1, "
