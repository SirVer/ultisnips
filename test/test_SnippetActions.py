from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class SnippetActions_PreActionModifiesBuffer(_VimTest):
    files = { 'us/all.snippets': r"""
        pre_expand "buffer[line:line] = ['\n']"
        snippet a "desc" "True" e
        abc
        endsnippet
        """}
    keys = 'a' + EX
    wanted = '\nabc'


class SnippetActions_PostActionModifiesBuffer(_VimTest):
    files = { 'us/all.snippets': r"""
        post_expand "buffer[line+1:line+1] = ['\n']"
        snippet a "desc" "True" e
        abc
        endsnippet
        """}
    keys = 'a' + EX
    wanted = 'abc\n'

class SnippetActions_ErrorOnBufferModificationThroughCommand(_VimTest):
    files = { 'us/all.snippets': r"""
        pre_expand "vim.command('normal O')"
        snippet a "desc" "True" e
        abc
        endsnippet
        """}
    keys = 'a' + EX
    expected_error = 'changes are untrackable'


class SnippetActions_ErrorOnModificationSnippetLine(_VimTest):
    files = { 'us/all.snippets': r"""
        post_expand "vim.command('normal dd')"
        snippet i "desc" "True" e
        if:
            $1
        endsnippet
        """}
    keys = 'i' + EX
    expected_error = 'line under the cursor was modified'


class SnippetActions_EnsureIndent(_VimTest):
    files = { 'us/all.snippets': r"""
        pre_expand "buffer[line] = ' '*4; new_cursor = (cursor[0], 4)"
        snippet i "desc" "True" e
        if:
            $1
        endsnippet
        """}
    keys = '\ni' + EX + 'i' + EX + 'x'
    wanted = """
    if:
    if:
        x"""


class SnippetActions_PostActionCanUseSnippetRange(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def ensure_newlines(start, end):
            buffer[start[0]:start[0]] = ['\n'] * 2
            buffer[end[0]+1:end[0]+1] = ['\n'] * 1
        endglobal

        post_expand "ensure_newlines(snippet_start, snippet_end)"
        snippet i "desc"
        if
            $1
        else
            $2
        end
        endsnippet
        """}
    keys = '\ni' + EX + 'x' + JF + 'y'
    wanted = """


if
    x
else
    y
end
"""


class SnippetActions_CanModifyParentBody(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def ensure_newlines(start, end):
            buffer[start[0]:start[0]] = ['\n'] * 2
        endglobal

        post_expand "ensure_newlines(snippet_start, snippet_end)"
        snippet i "desc"
        if
            $1
        else
            $2
        end
        endsnippet
        """}
    keys = '\ni' + EX + 'i' + EX + 'x' + JF + 'y' + JF + JF + 'z'
    wanted = """


if


    if
        x
    else
        y
    end
else
    z
end"""


class SnippetActions_MoveParentSnippetFromChildInPreAction(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def insert_import():
            buffer[2:2] = ['import smthing', '']
        endglobal

        pre_expand "insert_import()"
        snippet p "desc"
        print(smthing.traceback())
        endsnippet

        snippet i "desc"
        if
            $1
        else
            $2
        end
        endsnippet
        """}
    keys = 'i' + EX + 'p' + EX + JF + 'z'
    wanted = """import smthing

if
    print(smthing.traceback())
else
    z
end"""


class SnippetActions_CanExpandSnippetInDifferentPlace(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def expand_after_if():
            global new_cursor
            buffer[line] = buffer[line][:column] + buffer[line][column+1:]
            new_cursor = (line, buffer[line].index('if ')+3)
        endglobal

        pre_expand "expand_after_if()"
        snippet n "append not to if" w
        not $0
        endsnippet

        snippet i "if cond" w
        if $1: $2
        endsnippet
        """}
    keys = 'i' + EX + 'blah' + JF + 'n' + EX + JF + 'pass'
    wanted = """if not blah: pass"""


class SnippetActions_MoveVisual(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def extract_method():
            global new_cursor
            del buffer[line]
            buffer[len(buffer)-1:len(buffer)-1] = ['']
            new_cursor = (len(buffer)-2, 0)
        endglobal

        pre_expand "extract_method()"
        snippet n "append not to if" w
        def $1:
            ${VISUAL}

        endsnippet
        """}

    keys = """
def a:
    x()
    y()
    z()""" + ESC + 'kVk' + EX + 'n' + EX + 'b'

    wanted = """
def a:
    z()

def b:
    x()
    y()"""


class SnippetActions_CanMirrorTabStopsOutsideOfSnippet(_VimTest):
    files = { 'us/all.snippets': r"""
        post_jump "buffer[2] = 'debug({})'.format(tabstops[1].current_text)"
        snippet i "desc"
        if $1:
            $2
        endsnippet
        """}
    keys = """
---
i""" + EX + "test(some(complex(cond(a))))" + JF + "x"
    wanted = """debug(test(some(complex(cond(a)))))
---
if test(some(complex(cond(a)))):
    x"""


class SnippetActions_CanExpandAnonSnippetInJumpAction(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def expand_anon():
            if tabstop == 0:
                from UltiSnips import UltiSnips_Manager
                UltiSnips_Manager.expand_anon("a($2, $1)")
                return 'keep'
        endglobal

        post_jump "new_cursor = expand_anon()"
        snippet i "desc"
        if ${1:cond}:
            $0
        endsnippet
        """}
    keys = "i" + EX + "x" + JF + "1" + JF + "2" + JF + ";"
    wanted = """if x:
    a(2, 1);"""


class SnippetActions_CanExpandAnonSnippetInJumpActionWhileSelected(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def expand_anon():
            if tabstop == 0:
                from UltiSnips import UltiSnips_Manager
                UltiSnips_Manager.expand_anon(" // a($2, $1)")
                return 'keep'
        endglobal

        post_jump "new_cursor = expand_anon()"
        snippet i "desc"
        if ${1:cond}:
            ${2:pass}
        endsnippet
        """}
    keys = "i" + EX + "x" + JF + JF + "1" + JF + "2" + JF + ";"
    wanted = """if x:
    pass // a(2, 1);"""


class SnippetActions_CanUseContextFromContextMatch(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def expand_anon():
            if tabstop == 0:
                from UltiSnips import UltiSnips_Manager
                UltiSnips_Manager.expand_anon(" // a($2, $1)")
                return 'keep'
        endglobal

        pre_expand "buffer[line:line] = [context]"
        snippet i "desc" "'some context'" e
        body
        endsnippet
        """}
    keys = "i" + EX
    wanted = """some context
body"""
