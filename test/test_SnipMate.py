# encoding: utf-8
from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class snipMate_SimpleSnippet(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet hello
\tThis is a test snippet
\t# With a comment"""
    }
    keys = "hello" + EX
    wanted = "This is a test snippet\n# With a comment"


class snipMate_Disabled(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet hello
\tThis is a test snippet
\t# With a comment"""
    }
    keys = "hello" + EX
    wanted = "hello" + EX

    def _extra_vim_config(self, vim_config):
        vim_config.append("let g:UltiSnipsEnableSnipMate=0")


class snipMate_OtherFiletype(_VimTest):
    files = {
        "snippets/blubi.snippets": """
snippet hello
\tworked"""
    }
    keys = "hello" + EX + ESC + ":set ft=blubi\nohello" + EX
    wanted = "hello" + EX + "\nworked"


class snipMate_MultiMatches(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet hello The first snippet."
\tone
snippet hello The second snippet.
\ttwo"""
    }
    keys = "hello" + EX + "2\n"
    wanted = "two"


class snipMate_SimpleSnippetSubDirectory(_VimTest):
    files = {
        "snippets/_/blub.snippets": """
snippet hello
\tThis is a test snippet"""
    }
    keys = "hello" + EX
    wanted = "This is a test snippet"


class snipMate_SimpleSnippetInSnippetFile(_VimTest):
    files = {
        "snippets/_/hello.snippet": """This is a stand alone snippet""",
        "snippets/_/hello1.snippet": """This is two stand alone snippet""",
        "snippets/_/hello2/this_is_my_cool_snippet.snippet": """Three""",
    }
    keys = "hello" + EX + "\nhello1" + EX + "\nhello2" + EX
    wanted = "This is a stand alone snippet\nThis is two stand alone snippet\nThree"


class snipMate_Interpolation(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet test
\tla`printf('c%02d', 3)`lu"""
    }
    keys = "test" + EX
    wanted = "lac03lu"


class snipMate_InterpolationWithSystem(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet test
\tla`system('echo -ne öäü')`lu"""
    }
    keys = "test" + EX
    wanted = "laöäülu"


class snipMate_TestMirrors(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet for
\tfor (${2:i}; $2 < ${1:count}; $1++) {
\t\t${4}
\t}"""
    }
    keys = "for" + EX + "blub" + JF + "j" + JF + "hi"
    wanted = "for (j; j < blub; blub++) {\n\thi\n}"


class snipMate_TestNoBraceTabstops(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet test
\t$1 is $2"""
    }
    keys = "test" + EX + "blub" + JF + "blah"
    wanted = "blub is blah"


class snipMate_TestNoBraceTabstopsAndMirrors(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet test
\t$1 is $1, $2 is ${2}"""
    }
    keys = "test" + EX + "blub" + JF + "blah"
    wanted = "blub is blub, blah is blah"


class snipMate_TestMirrorsInPlaceholders(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet opt
\t<option value="${1:option}">${2:$1}</option>"""
    }
    keys = "opt" + EX + "some" + JF + JF + "ende"
    wanted = """<option value="some">some</option>ende"""


class snipMate_TestMirrorsInPlaceholders_Overwrite(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet opt
\t<option value="${1:option}">${2:$1}</option>"""
    }
    keys = "opt" + EX + "some" + JF + "not" + JF + "ende"
    wanted = """<option value="some">not</option>ende"""


class snipMate_Visual_Simple(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet v
\th${VISUAL}b"""
    }
    keys = "blablub" + ESC + "0v6l" + EX + "v" + EX
    wanted = "hblablubb"


class snipMate_NoNestedTabstops(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet test
\th$${1:${2:blub}}$$"""
    }
    keys = "test" + EX + JF + "hi"
    wanted = "h$${2:blub}$$hi"


class snipMate_Extends(_VimTest):
    files = {
        "snippets/a.snippets": """
extends b
snippet test
\tblub""",
        "snippets/b.snippets": """
snippet test1
\tblah""",
    }
    keys = ESC + ":set ft=a\n" + "itest1" + EX
    wanted = "blah"


class snipMate_EmptyLinesContinueSnippets(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet test
\tblub

\tblah

snippet test1
\ta"""
    }
    keys = "test" + EX
    wanted = "blub\n\nblah\n"


class snipMate_OverwrittenByRegExpTrigger(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet def
\tsnipmate
""",
        "us/all.snippets": r"""
snippet "(de)?f" "blub" r
ultisnips
endsnippet
""",
    }
    keys = "def" + EX
    wanted = "ultisnips"


class snipMate_Issue658(_VimTest):
    files = {
        "snippets/_.snippets": """
snippet /*
\t/*
\t * ${0}
\t */
"""
    }
    keys = ESC + ":set fo=r\n" + "i/*" + EX + "1\n2"
    wanted = """/*
 * 1
 * 2
 */
"""
