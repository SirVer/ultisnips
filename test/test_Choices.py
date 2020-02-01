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


class Choices_EmptyChoiceWillBeDiscarded(_VimTest):
    snippets = ("test", "${1|a,,c|}")
    keys = "test" + EX
    wanted = "1.a|2.c"


class Choices_WillNotExpand_If_ChoiceListIsEmpty(_VimTest):
    snippets = ("test", "${1||}")
    keys = "test" + EX
    wanted = "||"

