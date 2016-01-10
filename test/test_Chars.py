# encoding: utf-8
from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *
from test.util import running_on_windows

# Quotes in Snippets  {{{#
# Test for Bug #774917


def _snip_quote(qt):
    return (
        ('te' + qt + 'st', 'Expand me' + qt + '!', 'test: ' + qt),
        ('te', 'Bad', ''),
    )


class Snippet_With_SingleQuote(_VimTest):
    snippets = _snip_quote("'")
    keys = "te'st" + EX
    wanted = "Expand me'!"


class Snippet_With_SingleQuote_List(_VimTest):
    snippets = _snip_quote("'")
    keys = 'te' + LS + '2\n'
    wanted = "Expand me'!"


class Snippet_With_DoubleQuote(_VimTest):
    snippets = _snip_quote('"')
    keys = 'te"st' + EX
    wanted = "Expand me\"!"


class Snippet_With_DoubleQuote_List(_VimTest):
    snippets = _snip_quote('"')
    keys = 'te' + LS + '2\n'
    wanted = "Expand me\"!"

# End: Quotes in Snippets  #}}}

# Trailing whitespace {{{#


class RemoveTrailingWhitespace(_VimTest):
    snippets = ('test', """Hello\t ${1:default}\n$2""", '', 's')
    wanted = """Hello\nGoodbye"""
    keys = 'test' + EX + BS + JF + 'Goodbye'

class TrimSpacesAtEndOfLines(_VimTest):
    snippets = ('test', """next line\n\nshould be empty""", '', 'm')
    wanted = """\tnext line\n\n\tshould be empty"""
    keys = '\ttest' + EX

class DoNotTrimSpacesAtEndOfLinesByDefault(_VimTest):
    snippets = ('test', """next line\n\nshould be empty""", '', '')
    wanted = """\tnext line\n\t\n\tshould be empty"""
    keys = '\ttest' + EX


class LeaveTrailingWhitespace(_VimTest):
    snippets = ('test', """Hello \t ${1:default}\n$2""")
    wanted = """Hello \t \nGoodbye"""
    keys = 'test' + EX + BS + JF + 'Goodbye'
# End: Trailing whitespace #}}}

# Newline in default text {{{#
# Tests for bug 616315 #


class TrailingNewline_TabStop_NLInsideStuffBehind(_VimTest):
    snippets = ('test', r"""
x${1:
}<-behind1
$2<-behind2""")
    keys = 'test' + EX + 'j' + JF + 'k'
    wanted = """
xj<-behind1
k<-behind2"""


class TrailingNewline_TabStop_JustNL(_VimTest):
    snippets = ('test', r"""
x${1:
}
$2""")
    keys = 'test' + EX + 'j' + JF + 'k'
    wanted = """
xj
k"""


class TrailingNewline_TabStop_EndNL(_VimTest):
    snippets = ('test', r"""
x${1:a
}
$2""")
    keys = 'test' + EX + 'j' + JF + 'k'
    wanted = """
xj
k"""


class TrailingNewline_TabStop_StartNL(_VimTest):
    snippets = ('test', r"""
x${1:
a}
$2""")
    keys = 'test' + EX + 'j' + JF + 'k'
    wanted = """
xj
k"""


class TrailingNewline_TabStop_EndStartNL(_VimTest):
    snippets = ('test', r"""
x${1:
a
}
$2""")
    keys = 'test' + EX + 'j' + JF + 'k'
    wanted = """
xj
k"""


class TrailingNewline_TabStop_NotEndStartNL(_VimTest):
    snippets = ('test', r"""
x${1:a
a}
$2""")
    keys = 'test' + EX + 'j' + JF + 'k'
    wanted = """
xj
k"""


class TrailingNewline_TabStop_ExtraNL_ECR(_VimTest):
    snippets = ('test', r"""
x${1:a
a}
$2
""")
    keys = 'test' + EX + 'j' + JF + 'k'
    wanted = """
xj
k
"""


class _MultiLineDefault(_VimTest):
    snippets = ('test', r"""
x${1:a
b
c
d
e
f}
$2""")


class MultiLineDefault_Jump(_MultiLineDefault):
    keys = 'test' + EX + JF + 'y'
    wanted = """
xa
b
c
d
e
f
y"""


class MultiLineDefault_Type(_MultiLineDefault):
    keys = 'test' + EX + 'z' + JF + 'y'
    wanted = """
xz
y"""


class MultiLineDefault_BS(_MultiLineDefault):
    keys = 'test' + EX + BS + JF + 'y'
    wanted = """
x
y"""

# End: Newline in default text  #}}}

# Umlauts and Special Chars  {{{#


class _UmlautsBase(_VimTest):
    # SendKeys can't send UTF characters
    skip_if = lambda self: running_on_windows()


class Snippet_With_Umlauts_List(_UmlautsBase):
    snippets = _snip_quote('ü')
    keys = 'te' + LS + '2\n'
    wanted = 'Expand meü!'


class Snippet_With_Umlauts(_UmlautsBase):
    snippets = _snip_quote('ü')
    keys = 'teüst' + EX
    wanted = 'Expand meü!'


class Snippet_With_Umlauts_TypeOn(_UmlautsBase):
    snippets = ('ül', 'üüüüüßßßß')
    keys = 'te ül' + EX + 'more text'
    wanted = 'te üüüüüßßßßmore text'


class Snippet_With_Umlauts_OverwriteFirst(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü ${2:hello}ßß\nüüüü')
    keys = 'te ül' + EX + 'more text' + JF + JF + 'end'
    wanted = 'te üü more text üü helloßß\nüüüüend'


class Snippet_With_Umlauts_OverwriteSecond(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü ${2:hello}ßß\nüüüü')
    keys = 'te ül' + EX + JF + 'more text' + JF + 'end'
    wanted = 'te üü world üü more textßß\nüüüüend'


class Snippet_With_Umlauts_OverwriteNone(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü ${2:hello}ßß\nüüüü')
    keys = 'te ül' + EX + JF + JF + 'end'
    wanted = 'te üü world üü helloßß\nüüüüend'


class Snippet_With_Umlauts_Mirrors(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü $1')
    keys = 'te ül' + EX + 'hello'
    wanted = 'te üü hello üü hello'


class Snippet_With_Umlauts_Python(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü `!p snip.rv = len(t[1])*"a"`')
    keys = 'te ül' + EX + 'hüüll'
    wanted = 'te üü hüüll üü aaaaa'

class UmlautsBeforeTriggerAndCharsAfter(_UmlautsBase):
    snippets = ('trig', 'success')
    keys = 'ööuu trig b' + 2 * ARR_L + EX
    wanted = 'ööuu success b'

class NoUmlautsBeforeTriggerAndCharsAfter(_UmlautsBase):
    snippets = ('trig', 'success')
    keys = 'oouu trig b' + 2 * ARR_L + EX
    wanted = 'oouu success b'

# End: Umlauts and Special Chars  #}}}
