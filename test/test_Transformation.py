# encoding: utf-8
from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *
from test.util import no_unidecode_available

# Transformations  {{{#


class Transformation_SimpleCase_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/foo/batzl/}')
    keys = 'test' + EX + 'hallo foo boy'
    wanted = 'hallo foo boy hallo batzl boy'


class Transformation_SimpleCaseNoTransform_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/foo/batzl/}')
    keys = 'test' + EX + 'hallo'
    wanted = 'hallo hallo'


class Transformation_SimpleCaseTransformInFront_ExpectCorrectResult(_VimTest):
    snippets = ('test', '${1/foo/batzl/} $1')
    keys = 'test' + EX + 'hallo foo'
    wanted = 'hallo batzl hallo foo'


class Transformation_SimpleCaseTransformInFrontDefVal_ECR(_VimTest):
    snippets = ('test', '${1/foo/batzl/} ${1:replace me}')
    keys = 'test' + EX + 'hallo foo'
    wanted = 'hallo batzl hallo foo'


class Transformation_MultipleTransformations_ECR(_VimTest):
    snippets = ('test', '${1:Some Text}${1/.+/\\U$0\E/}\n${1/.+/\L$0\E/}')
    keys = 'test' + EX + 'SomE tExt '
    wanted = 'SomE tExt SOME TEXT \nsome text '


class Transformation_TabIsAtEndAndDeleted_ECR(_VimTest):
    snippets = ('test', '${1/.+/is something/}${1:some}')
    keys = 'hallo test' + EX + 'some\b\b\b\b\b'
    wanted = 'hallo '


class Transformation_TabIsAtEndAndDeleted1_ECR(_VimTest):
    snippets = ('test', '${1/.+/is something/}${1:some}')
    keys = 'hallo test' + EX + 'some\b\b\b\bmore'
    wanted = 'hallo is somethingmore'


class Transformation_TabIsAtEndNoTextLeave_ECR(_VimTest):
    snippets = ('test', '${1/.+/is something/}${1}')
    keys = 'hallo test' + EX
    wanted = 'hallo '


class Transformation_TabIsAtEndNoTextType_ECR(_VimTest):
    snippets = ('test', '${1/.+/is something/}${1}')
    keys = 'hallo test' + EX + 'b'
    wanted = 'hallo is somethingb'


class Transformation_InsideTabLeaveAtDefault_ECR(_VimTest):
    snippets = ('test', r"$1 ${2:${1/.+/(?0:defined $0)/}}")
    keys = 'test' + EX + 'sometext' + JF
    wanted = 'sometext defined sometext'


class Transformation_InsideTabOvertype_ECR(_VimTest):
    snippets = ('test', r"$1 ${2:${1/.+/(?0:defined $0)/}}")
    keys = 'test' + EX + 'sometext' + JF + 'overwrite'
    wanted = 'sometext overwrite'


class Transformation_Backreference_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/([ab])oo/$1ull/}')
    keys = 'test' + EX + 'foo boo aoo'
    wanted = 'foo boo aoo foo bull aoo'


class Transformation_BackreferenceTwice_ExpectCorrectResult(_VimTest):
    snippets = ('test', r"$1 ${1/(dead) (par[^ ]*)/this $2 is a bit $1/}")
    keys = 'test' + EX + 'dead parrot'
    wanted = 'dead parrot this parrot is a bit dead'


class Transformation_CleverTransformUpercaseChar_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/(.)/\\u$1/}')
    keys = 'test' + EX + 'hallo'
    wanted = 'hallo Hallo'


class Transformation_CleverTransformLowercaseChar_ExpectCorrectResult(
        _VimTest):
    snippets = ('test', '$1 ${1/(.*)/\l$1/}')
    keys = 'test' + EX + 'Hallo'
    wanted = 'Hallo hallo'


class Transformation_CleverTransformLongUpper_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/(.*)/\\U$1\E/}')
    keys = 'test' + EX + 'hallo'
    wanted = 'hallo HALLO'


class Transformation_CleverTransformLongLower_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/(.*)/\L$1\E/}')
    keys = 'test' + EX + 'HALLO'
    wanted = 'HALLO hallo'


class Transformation_SimpleCaseAsciiResult(_VimTest):
    skip_if = lambda self: no_unidecode_available()
    snippets = ('ascii', '$1 ${1/(.*)/$1/a}')
    keys = 'ascii' + EX + 'éèàçôïÉÈÀÇÔÏ€'
    wanted = 'éèàçôïÉÈÀÇÔÏ€ eeacoiEEACOIEU'


class Transformation_LowerCaseAsciiResult(_VimTest):
    skip_if = lambda self: no_unidecode_available()
    snippets = ('ascii', '$1 ${1/(.*)/\L$1\E/a}')
    keys = 'ascii' + EX + 'éèàçôïÉÈÀÇÔÏ€'
    wanted = 'éèàçôïÉÈÀÇÔÏ€ eeacoieeacoieu'


class Transformation_ConditionalInsertionSimple_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/(^a).*/(?0:began with an a)/}')
    keys = 'test' + EX + 'a some more text'
    wanted = 'a some more text began with an a'


class Transformation_CIBothDefinedNegative_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}')
    keys = 'test' + EX + 'b some'
    wanted = 'b some no'


class Transformation_CIBothDefinedPositive_ExpectCorrectResult(_VimTest):
    snippets = ('test', '$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}')
    keys = 'test' + EX + 'a some'
    wanted = 'a some yes'


class Transformation_ConditionalInsertRWEllipsis_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/(\w+(?:\W+\w+){,7})\W*(.+)?/$1(?2:...)/}")
    keys = 'test' + EX + 'a b  c d e f ghhh h oha'
    wanted = 'a b  c d e f ghhh h oha a b  c d e f ghhh h...'


class Transformation_ConditionalInConditional_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/^.*?(-)?(>)?$/(?2::(?1:>:.))/}")
    keys = 'test' + EX + 'hallo' + ESC + '$a\n' + \
           'test' + EX + 'hallo-' + ESC + '$a\n' + \
           'test' + EX + 'hallo->'
    wanted = 'hallo .\nhallo- >\nhallo-> '


class Transformation_CINewlines_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/, */\n/}")
    keys = 'test' + EX + 'test, hallo'
    wanted = 'test, hallo test\nhallo'


class Transformation_CITabstop_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/, */\t/}")
    keys = 'test' + EX + 'test, hallo'
    wanted = 'test, hallo test\thallo'


class Transformation_CIEscapedParensinReplace_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/hal((?:lo)|(?:ul))/(?1:ha\($1\))/}")
    keys = 'test' + EX + 'test, halul'
    wanted = 'test, halul test, ha(ul)'


class Transformation_OptionIgnoreCase_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/test/blah/i}")
    keys = 'test' + EX + 'TEST'
    wanted = 'TEST blah'


class Transformation_OptionMultiline_ECR(_VimTest):
    snippets = ('test', r"${VISUAL/^/* /mg}")
    keys = 'test\ntest\ntest' + ESC + 'V2k' + EX + 'test' + EX
    wanted = '* test\n* test\n* test'


class Transformation_OptionReplaceGlobal_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/, */-/g}")
    keys = 'test' + EX + 'a, nice, building'
    wanted = 'a, nice, building a-nice-building'


class Transformation_OptionReplaceGlobalMatchInReplace_ECR(_VimTest):
    snippets = ('test', r"$1 ${1/, */, /g}")
    keys = 'test' + EX + 'a, nice,   building'
    wanted = 'a, nice,   building a, nice, building'


class TransformationUsingBackspaceToDeleteDefaultValueInFirstTab_ECR(_VimTest):
    snippets = ('test', 'snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} '
                '${1:default} ${2:def}')
    keys = 'test' + EX + BS + JF + 'hi'
    wanted = 'snip  m2  hi'


class TransformationUsingBackspaceToDeleteDefaultValueInSecondTab_ECR(
        _VimTest):
    snippets = ('test', 'snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} '
                '${1:default} ${2:def}')
    keys = 'test' + EX + 'hi' + JF + BS
    wanted = 'snip m1  hi '


class TransformationUsingBackspaceToDeleteDefaultValueTypeSomethingThen_ECR(
        _VimTest):
    snippets = ('test', 'snip ${1/.+/(?0:matched)/} ${1:default}')
    keys = 'test' + EX + BS + 'hallo'
    wanted = 'snip matched hallo'


class TransformationUsingBackspaceToDeleteDefaultValue_ECR(_VimTest):
    snippets = ('test', 'snip ${1/.+/(?0:matched)/} ${1:default}')
    keys = 'test' + EX + BS
    wanted = 'snip  '


class Transformation_TestKill_InsertBefore_NoKill(_VimTest):
    snippets = 'test', r"$1 ${1/.*/\L$0$0\E/}_"
    keys = 'hallo test' + EX + 'AUCH' + ESC + \
        'wihi' + ESC + 'bb' + 'ino' + JF + 'end'
    wanted = 'hallo noAUCH hinoauchnoauch_end'


class Transformation_TestKill_InsertAfter_NoKill(_VimTest):
    snippets = 'test', r"$1 ${1/.*/\L$0$0\E/}_"
    keys = 'hallo test' + EX + 'AUCH' + ESC + \
        'eiab' + ESC + 'bb' + 'ino' + JF + 'end'
    wanted = 'hallo noAUCH noauchnoauchab_end'


class Transformation_TestKill_InsertBeginning_Kill(_VimTest):
    snippets = 'test', r"$1 ${1/.*/\L$0$0\E/}_"
    keys = 'hallo test' + EX + 'AUCH' + ESC + \
        'wahi' + ESC + 'bb' + 'ino' + JF + 'end'
    wanted = 'hallo noAUCH ahiuchauch_end'


class Transformation_TestKill_InsertEnd_Kill(_VimTest):
    snippets = 'test', r"$1 ${1/.*/\L$0$0\E/}_"
    keys = 'hallo test' + EX + 'AUCH' + ESC + \
        'ehihi' + ESC + 'bb' + 'ino' + JF + 'end'
    wanted = 'hallo noAUCH auchauchih_end'

class Transformation_ConditionalWithEscapedDelimiter(_VimTest):
    snippets = 'test', r"$1 ${1/(aa)|.*/(?1:yes\:no\))/}"
    keys = 'test' + EX + 'aa'
    wanted = 'aa yes:no)'

class Transformation_ConditionalWithBackslashBeforeDelimiter(_VimTest):
    snippets = 'test', r"$1 ${1/(aa)|.*/(?1:yes\\:no)/}"
    keys = 'test' + EX + 'aa'
    wanted = 'aa yes\\'

class Transformation_ConditionalWithBackslashBeforeDelimiter1(_VimTest):
    snippets = 'test', r"$1 ${1/(aa)|.*/(?1:yes:no\\)/}"
    keys = 'test' + EX + 'ab'
    wanted = 'ab no\\'
# End: Transformations  #}}}
