from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Recursive (Nested) Snippets  {{{#


class RecTabStops_SimpleCase_ExpectCorrectResult(_VimTest):
    snippets = ('m', '[ ${1:first}  ${2:sec} ]')
    keys = 'm' + EX + 'm' + EX + 'hello' + \
        JF + 'world' + JF + 'ups' + JF + 'end'
    wanted = '[ [ hello  world ]ups  end ]'


class RecTabStops_SimpleCaseLeaveSecondSecond_ExpectCorrectResult(_VimTest):
    snippets = ('m', '[ ${1:first}  ${2:sec} ]')
    keys = 'm' + EX + 'm' + EX + 'hello' + JF + 'world' + JF + JF + JF + 'end'
    wanted = '[ [ hello  world ]  sec ]end'


class RecTabStops_SimpleCaseLeaveFirstSecond_ExpectCorrectResult(_VimTest):
    snippets = ('m', '[ ${1:first}  ${2:sec} ]')
    keys = 'm' + EX + 'm' + EX + 'hello' + JF + JF + JF + 'world' + JF + 'end'
    wanted = '[ [ hello  sec ]  world ]end'


class RecTabStops_InnerWOTabStop_ECR(_VimTest):
    snippets = (
        ('m1', 'Just some Text'),
        ('m', '[ ${1:first}  ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm1' + EX + 'hi' + JF + 'two' + JF + 'end'
    wanted = '[ Just some Texthi  two ]end'


class RecTabStops_InnerWOTabStopTwiceDirectly_ECR(_VimTest):
    snippets = (
        ('m1', 'JST'),
        ('m', '[ ${1:first}  ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm1' + EX + ' m1' + EX + 'hi' + JF + 'two' + JF + 'end'
    wanted = '[ JST JSThi  two ]end'


class RecTabStops_InnerWOTabStopTwice_ECR(_VimTest):
    snippets = (
        ('m1', 'JST'),
        ('m', '[ ${1:first}  ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm1' + EX + JF + 'm1' + EX + 'hi' + JF + 'end'
    wanted = '[ JST  JSThi ]end'


class RecTabStops_OuterOnlyWithZeroTS_ECR(_VimTest):
    snippets = (
        ('m', 'A $0 B'),
        ('m1', 'C $1 D $0 E'),
    )
    keys = 'm' + EX + 'm1' + EX + 'CD' + JF + 'DE'
    wanted = 'A C CD D DE E B'


class RecTabStops_OuterOnlyWithZero_ECR(_VimTest):
    snippets = (
        ('m', 'A $0 B'),
        ('m1', 'C $1 D $0 E'),
    )
    keys = 'm' + EX + 'm1' + EX + 'CD' + JF + 'DE'
    wanted = 'A C CD D DE E B'


class RecTabStops_ExpandedInZeroTS_ECR(_VimTest):
    snippets = (
        ('m', 'A $0 B $1'),
        ('m1', 'C $1 D $0 E'),
    )
    keys = 'm' + EX + 'hi' + JF + 'm1' + EX + 'CD' + JF + 'DE'
    wanted = 'A C CD D DE E B hi'


class RecTabStops_ExpandedInZeroTSTwice_ECR(_VimTest):
    snippets = (
        ('m', 'A $0 B $1'),
        ('m1', 'C $1 D $0 E'),
    )
    keys = 'm' + EX + 'hi' + JF + 'm' + EX + 'again' + JF + 'm1' + \
        EX + 'CD' + JF + 'DE'
    wanted = 'A A C CD D DE E B again B hi'


class RecTabStops_ExpandedInZeroTSSecondTime_ECR(_VimTest):
    snippets = (
        ('m', 'A $0 B $1'),
        ('m1', 'C $1 D $0 E'),
    )
    keys = 'm' + EX + 'hi' + JF + 'm' + EX + \
        'm1' + EX + 'CD' + JF + 'DE' + JF + 'AB'
    wanted = 'A A AB B C CD D DE E B hi'


class RecTabsStops_TypeInZero_ECR(_VimTest):
    snippets = (
        ('v', r"\vec{$1}", 'Vector', 'w'),
        ('frac', r"\frac{${1:one}}${0:zero}{${2:two}}", 'Fractio', 'w'),
    )
    keys = 'v' + EX + 'frac' + EX + 'a' + JF + 'b' + JF + 'frac' + EX + 'aa' + JF + JF + 'cc' + JF + \
        'hello frac' + EX + JF + JF + 'world'
    wanted = r"\vec{\frac{a}\frac{aa}cc{two}{b}}hello \frac{one}world{two}"


class RecTabsStops_TypeInZero2_ECR(_VimTest):
    snippets = (
        ('m', r"_${0:explicit zero}", 'snip', 'i'),
    )
    keys = 'm' + EX + 'hello m' + EX + 'world m' + EX + 'end'
    wanted = r"_hello _world _end"


class RecTabsStops_BackspaceZero_ECR(_VimTest):
    snippets = (
        ('m', r"${1:one}${0:explicit zero}${2:two}", 'snip', 'i'),
    )
    keys = 'm' + EX + JF + JF + BS + 'm' + EX
    wanted = r"oneoneexplicit zerotwotwo"


class RecTabStops_MirrorInnerSnippet_ECR(_VimTest):
    snippets = (
        ('m', '[ $1 $2 ] $1'),
        ('m1', 'ASnip $1 ASnip $2 ASnip'),
    )
    keys = 'm' + EX + 'm1' + EX + 'Hallo' + JF + 'Hi' + \
        JF + 'endone' + JF + 'two' + JF + 'totalend'
    wanted = '[ ASnip Hallo ASnip Hi ASnipendone two ] ASnip Hallo ASnip Hi ASnipendonetotalend'


class RecTabStops_NotAtBeginningOfTS_ExpectCorrectResult(_VimTest):
    snippets = ('m', '[ ${1:first}  ${2:sec} ]')
    keys = 'm' + EX + 'hello m' + EX + 'hi' + JF + 'two' + JF + 'ups' + JF + 'three' + \
        JF + 'end'
    wanted = '[ hello [ hi  two ]ups  three ]end'


class RecTabStops_InNewlineInTabstop_ExpectCorrectResult(_VimTest):
    snippets = ('m', '[ ${1:first}  ${2:sec} ]')
    keys = 'm' + EX + 'hello\nm' + EX + 'hi' + JF + 'two' + JF + 'ups' + JF + 'three' + \
        JF + 'end'
    wanted = '[ hello\n[ hi  two ]ups  three ]end'


class RecTabStops_InNewlineInTabstopNotAtBeginOfLine_ECR(_VimTest):
    snippets = ('m', '[ ${1:first}  ${2:sec} ]')
    keys = 'm' + EX + 'hello\nhello again m' + EX + 'hi' + JF + 'two' + \
        JF + 'ups' + JF + 'three' + JF + 'end'
    wanted = '[ hello\nhello again [ hi  two ]ups  three ]end'


class RecTabStops_InNewlineMultiline_ECR(_VimTest):
    snippets = ('m', 'M START\n$0\nM END')
    keys = 'm' + EX + 'm' + EX
    wanted = 'M START\nM START\n\nM END\nM END'


class RecTabStops_InNewlineManualIndent_ECR(_VimTest):
    snippets = ('m', 'M START\n$0\nM END')
    keys = 'm' + EX + '    m' + EX + 'hi'
    wanted = 'M START\n    M START\n    hi\n    M END\nM END'


class RecTabStops_InNewlineManualIndentTextInFront_ECR(_VimTest):
    snippets = ('m', 'M START\n$0\nM END')
    keys = 'm' + EX + '    hallo m' + EX + 'hi'
    wanted = 'M START\n    hallo M START\n    hi\n    M END\nM END'


class RecTabStops_InNewlineMultilineWithIndent_ECR(_VimTest):
    snippets = ('m', 'M START\n    $0\nM END')
    keys = 'm' + EX + 'm' + EX + 'hi'
    wanted = 'M START\n    M START\n        hi\n    M END\nM END'


class RecTabStops_InNewlineMultilineWithNonZeroTS_ECR(_VimTest):
    snippets = ('m', 'M START\n    $1\nM END -> $0')
    keys = 'm' + EX + 'm' + EX + 'hi' + JF + 'hallo' + JF + 'end'
    wanted = 'M START\n    M START\n        hi\n    M END -> hallo\n' \
        'M END -> end'


class RecTabStops_BarelyNotLeavingInner_ECR(_VimTest):
    snippets = (
        ('m', '[ ${1:first} ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm' + EX + 'a' + 3 * ARR_L + JF + 'hallo' + \
        JF + 'ups' + JF + 'world' + JF + 'end'
    wanted = '[ [ a hallo ]ups world ]end'


class RecTabStops_LeavingInner_ECR(_VimTest):
    snippets = (
        ('m', '[ ${1:first} ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm' + EX + 'a' + 4 * ARR_L + JF + 'hallo' + \
        JF + 'world'
    wanted = '[ [ a sec ] hallo ]world'


class RecTabStops_LeavingInnerInner_ECR(_VimTest):
    snippets = (
        ('m', '[ ${1:first} ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm' + EX + 'm' + EX + 'a' + 4 * ARR_L + JF + 'hallo' + \
        JF + 'ups' + JF + 'world' + JF + 'end'
    wanted = '[ [ [ a sec ] hallo ]ups world ]end'


class RecTabStops_LeavingInnerInnerTwo_ECR(_VimTest):
    snippets = (
        ('m', '[ ${1:first} ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm' + EX + 'm' + EX + 'a' + 6 * ARR_L + JF + 'hallo' + \
        JF + 'end'
    wanted = '[ [ [ a sec ] sec ] hallo ]end'


class RecTabStops_ZeroTSisNothingSpecial_ECR(_VimTest):
    snippets = (
        ('m1', '[ ${1:first} $0 ${2:sec} ]'),
        ('m', '[ ${1:first} ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm1' + EX + 'one' + JF + 'two' + \
        JF + 'three' + JF + 'four' + JF + 'end'
    wanted = '[ [ one three two ] four ]end'


class RecTabStops_MirroredZeroTS_ECR(_VimTest):
    snippets = (
        ('m1', '[ ${1:first} ${0:Year, some default text} $0 ${2:sec} ]'),
        ('m', '[ ${1:first} ${2:sec} ]'),
    )
    keys = 'm' + EX + 'm1' + EX + 'one' + JF + 'two' + \
        JF + 'three' + JF + 'four' + JF + 'end'
    wanted = '[ [ one three three two ] four ]end'


class RecTabStops_ChildTriggerContainsParentTextObjects(_VimTest):
    # https://bugs.launchpad.net/bugs/1191617
    files = { 'us/all.snippets': r"""
global !p
def complete(t, opts):
 if t:
   opts = [ q[len(t):] for q in opts if q.startswith(t) ]
 if len(opts) == 0:
   return ''
 return opts[0] if len(opts) == 1 else "(" + '|'.join(opts) + ')'
def autocomplete_options(t, string, attr=None):
   return complete(t[1], [opt for opt in attr if opt not in string])
endglobal
snippet /form_for(.*){([^|]*)/ "form_for html options" rw!
`!p
auto = autocomplete_options(t, match.group(2), attr=["id: ", "class: ", "title:  "])
snip.rv = "form_for" + match.group(1) + "{"`$1`!p if (snip.c != auto) : snip.rv=auto`
endsnippet
"""}
    keys = 'form_for user, namespace: some_namespace, html: {i' + EX + 'i' + EX
    wanted = 'form_for user, namespace: some_namespace, html: {(id: |class: |title:  )d: '
# End: Recursive (Nested) Snippets  #}}}
