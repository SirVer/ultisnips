from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class ContextSnippets_SimpleSnippet(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet a "desc" "True" e
        abc
        endsnippet
        """}
    keys = 'a' + EX
    wanted = 'abc'


class ContextSnippets_ExpandOnTrue(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def check_context():
            return True
        endglobal

        snippet a "desc" "check_context()" e
        abc
        endsnippet
        """}
    keys = 'a' + EX
    wanted = 'abc'


class ContextSnippets_DoNotExpandOnFalse(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def check_context():
            return False
        endglobal

        snippet a "desc" "check_context()" e
        abc
        endsnippet
        """}
    keys = 'a' + EX
    wanted = keys



class ContextSnippets_UseContext(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def wrap(ins):
            return "< " + ins + " >"
        endglobal

        snippet a "desc" "wrap(buffer[line-1])" e
        { `!p snip.rv = context` }
        endsnippet
        """}
    keys = 'a' + EX
    wanted = '{ < a > }'


class ContextSnippets_SnippetPriority(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet i "desc" "re.search('err :=', buffer[line-2])" e
        if err != nil {
            ${1:// pass}
        }
        endsnippet

        snippet i
        if ${1:true} {
            ${2:// pass}
        }
        endsnippet
        """}

    keys = r"""
        err := some_call()
        i""" + EX + JF +  """
        i""" + EX
    wanted = r"""
        err := some_call()
        if err != nil {
            // pass
        }
        if true {
            // pass
        }"""


class ContextSnippets_PriorityKeyword(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet i "desc" "True" e
        a
        endsnippet

        priority 100
        snippet i
        b
        endsnippet
        """}

    keys = "i" + EX
    wanted = "b"


class ContextSnippets_ReportError(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet e "desc" "Tru" e
        error
        endsnippet
        """}

    keys = "e" + EX
    wanted = "e" + EX
    expected_error = r"NameError: name 'Tru' is not defined"


class ContextSnippets_ReportErrorOnIndexOutOfRange(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet e "desc" "buffer[123]" e
        error
        endsnippet
        """}

    keys = "e" + EX
    wanted = "e" + EX
    expected_error = r"IndexError: line number out of range"
