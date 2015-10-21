from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class ParseSnippets_SimpleSnippet(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet testsnip "Test Snippet" b!
        This is a test snippet!
        endsnippet
        """}
    keys = 'testsnip' + EX
    wanted = 'This is a test snippet!'


class ParseSnippets_MissingEndSnippet(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet testsnip "Test Snippet" b!
        This is a test snippet!
        """}
    keys = 'testsnip' + EX
    wanted = 'testsnip' + EX
    expected_error = r"Missing 'endsnippet' for 'testsnip' in \S+:4"


class ParseSnippets_UnknownDirective(_VimTest):
    files = { 'us/all.snippets': r"""
        unknown directive
        """}
    keys = 'testsnip' + EX
    wanted = 'testsnip' + EX
    expected_error = r"Invalid line 'unknown directive' in \S+:2"


class ParseSnippets_InvalidPriorityLine(_VimTest):
    files = { 'us/all.snippets': r"""
        priority - 50
        """}
    keys = 'testsnip' + EX
    wanted = 'testsnip' + EX
    expected_error = r"Invalid priority '- 50' in \S+:2"


class ParseSnippets_InvalidPriorityLine1(_VimTest):
    files = { 'us/all.snippets': r"""
        priority
        """}
    keys = 'testsnip' + EX
    wanted = 'testsnip' + EX
    expected_error = r"Invalid priority '' in \S+:2"


class ParseSnippets_ExtendsWithoutFiletype(_VimTest):
    files = { 'us/all.snippets': r"""
        extends
        """}
    keys = 'testsnip' + EX
    wanted = 'testsnip' + EX
    expected_error = r"'extends' without file types in \S+:2"


class ParseSnippets_ClearAll(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet testsnip "Test snippet"
        This is a test.
        endsnippet

        clearsnippets
        """}
    keys = 'testsnip' + EX
    wanted = 'testsnip' + EX


class ParseSnippets_ClearOne(_VimTest):
    files = { 'us/all.snippets': r"""
        clearsnippets toclear

        snippet testsnip "Test snippet"
        This is a test.
        endsnippet

        snippet toclear "Snippet to clear"
        Do not expand.
        endsnippet
        """}
    keys = 'toclear' + EX + '\n' + 'testsnip' + EX
    wanted = 'toclear' + EX + '\n' + 'This is a test.'


class ParseSnippets_ClearTwo(_VimTest):
    files = { 'us/all.snippets': r"""
        clearsnippets testsnip toclear

        snippet testsnip "Test snippet"
        This is a test.
        endsnippet

        snippet toclear "Snippet to clear"
        Do not expand.
        endsnippet
        """}
    keys = 'toclear' + EX + '\n' + 'testsnip' + EX
    wanted = 'toclear' + EX + '\n' + 'testsnip' + EX


class _ParseSnippets_MultiWord(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet /test snip/
        This is a test.
        endsnippet

        snippet !snip test! "Another snippet"
        This is another test.
        endsnippet

        snippet "snippet test" "Another snippet" b
        This is yet another test.
        endsnippet
        """}


class ParseSnippets_MultiWord_Simple(_ParseSnippets_MultiWord):
    keys = 'test snip' + EX
    wanted = 'This is a test.'


class ParseSnippets_MultiWord_Description(_ParseSnippets_MultiWord):
    keys = 'snip test' + EX
    wanted = 'This is another test.'


class ParseSnippets_MultiWord_Description_Option(_ParseSnippets_MultiWord):
    keys = 'snippet test' + EX
    wanted = 'This is yet another test.'


class _ParseSnippets_MultiWord_RE(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet /[d-f]+/ "" r
        az test
        endsnippet

        snippet !^(foo|bar)$! "" r
        foo-bar test
        endsnippet

        snippet "(test ?)+" "" r
        re-test
        endsnippet
        """}


class ParseSnippets_MultiWord_RE1(_ParseSnippets_MultiWord_RE):
    keys = 'abc def' + EX
    wanted = 'abc az test'


class ParseSnippets_MultiWord_RE2(_ParseSnippets_MultiWord_RE):
    keys = 'foo' + EX + ' bar' + EX + '\nbar' + EX
    wanted = 'foo-bar test bar\t\nfoo-bar test'


class ParseSnippets_MultiWord_RE3(_ParseSnippets_MultiWord_RE):
    keys = 'test test test' + EX
    wanted = 're-test'


class ParseSnippets_MultiWord_Quotes(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet "test snip"
        This is a test.
        endsnippet
        """}
    keys = 'test snip' + EX
    wanted = 'This is a test.'


class ParseSnippets_MultiWord_WithQuotes(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet !"test snip"!
        This is a test.
        endsnippet
        """}
    keys = '"test snip"' + EX
    wanted = 'This is a test.'


class ParseSnippets_MultiWord_NoContainer(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet test snip
        This is a test.
        endsnippet
        """}
    keys = 'test snip' + EX
    wanted = keys
    expected_error = "Invalid multiword trigger: 'test snip' in \S+:2"


class ParseSnippets_MultiWord_UnmatchedContainer(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet !inv snip/
        This is a test.
        endsnippet
        """}
    keys = 'inv snip' + EX
    wanted = keys
    expected_error = "Invalid multiword trigger: '!inv snip/' in \S+:2"


class ParseSnippets_Global_Python(_VimTest):
    files = { 'us/all.snippets': r"""
        global !p
        def tex(ins):
            return "a " + ins + " b"
        endglobal

        snippet ab
        x `!p snip.rv = tex("bob")` y
        endsnippet

        snippet ac
        x `!p snip.rv = tex("jon")` y
        endsnippet
        """}
    keys = 'ab' + EX + '\nac' + EX
    wanted = 'x a bob b y\nx a jon b y'


class ParseSnippets_Global_Local_Python(_VimTest):
    files = { 'us/all.snippets': r"""
global !p
def tex(ins):
    return "a " + ins + " b"
endglobal

snippet ab
x `!p first = tex("bob")
snip.rv = "first"` `!p snip.rv = first` y
endsnippet
        """}
    keys = 'ab' + EX
    wanted = 'x first a bob b y'


class ParseSnippets_PrintPythonStacktrace(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet test
        `!p abc()`
        endsnippet
        """}
    keys = 'test' + EX
    wanted = keys
    expected_error = " > abc"


class ParseSnippets_PrintPythonStacktraceMultiline(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet test
        `!p if True:
            qwe()`
        endsnippet
        """}
    keys = 'test' + EX
    wanted = keys
    expected_error = " > \s+qwe"


class ParseSnippets_PrintErroneousSnippet(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet test "asd()" e
        endsnippet
        """}
    keys = 'test' + EX
    wanted = keys
    expected_error = "Trigger: test"


class ParseSnippets_PrintErroneousSnippetContext(_VimTest):
    files = { 'us/all.snippets': r"""
        snippet test "asd()" e
        endsnippet
        """}
    keys = 'test' + EX
    wanted = keys
    expected_error = "Context: asd"


class ParseSnippets_PrintErroneousSnippetPreAction(_VimTest):
    files = { 'us/all.snippets': r"""
        pre_expand "asd()"
        snippet test
        endsnippet
        """}
    keys = 'test' + EX
    wanted = keys
    expected_error = "Pre-expand: asd"


class ParseSnippets_PrintErroneousSnippetPostAction(_VimTest):
    files = { 'us/all.snippets': r"""
        post_expand "asd()"
        snippet test
        endsnippet
        """}
    keys = 'test' + EX
    wanted = keys
    expected_error = "Post-expand: asd"

class ParseSnippets_PrintErroneousSnippetLocation(_VimTest):
    files = { 'us/all.snippets': r"""
        post_expand "asd()"
        snippet test
        endsnippet
        """}
    keys = 'test' + EX
    wanted = keys
    expected_error = "Defined in: .*/all.snippets"
