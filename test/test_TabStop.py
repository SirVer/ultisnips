from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class TabStopSimpleReplace_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} ${1:Beginning}")
    keys = "hallo" + EX + "na" + JF + "Du Nase"
    wanted = "hallo Du Nase na"


class TabStopSimpleReplaceZeroLengthTabstops_ExpectCorrectResult(_VimTest):
    snippets = ("test", r":latex:\`$1\`$0")
    keys = "test" + EX + "Hello" + JF + "World"
    wanted = ":latex:`Hello`World"


class TabStopSimpleReplaceReversed_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${1:End} ${0:Beginning}")
    keys = "hallo" + EX + "na" + JF + "Du Nase"
    wanted = "hallo na Du Nase"


class TabStopSimpleReplaceSurrounded_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} a small feed")
    keys = "hallo" + EX + "Nase"
    wanted = "hallo Nase a small feed"


class TabStopSimpleReplaceSurrounded1_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 a small feed")
    keys = "hallo" + EX + "Nase"
    wanted = "hallo Nase a small feed"


class TabStop_Exit_ExpectCorrectResult(_VimTest):
    snippets = ("echo", "$0 run")
    keys = "echo" + EX + "test"
    wanted = "test run"


class TabStopNoReplace_ExpectCorrectResult(_VimTest):
    snippets = ("echo", "echo ${1:Hallo}")
    keys = "echo" + EX
    wanted = "echo Hallo"


class TabStop_EscapingCharsBackticks(_VimTest):
    snippets = ("test", r"snip \` literal")
    keys = "test" + EX
    wanted = "snip ` literal"


class TabStop_EscapingCharsDollars(_VimTest):
    snippets = ("test", r"snip \$0 $$0 end")
    keys = "test" + EX + "hi"
    wanted = "snip $0 $hi end"


class TabStop_EscapingCharsDollars1(_VimTest):
    snippets = ("test", r"a\${1:literal}")
    keys = "test" + EX
    wanted = "a${1:literal}"


class TabStop_EscapingCharsDollars_BeginningOfLine(_VimTest):
    snippets = ("test", "\n\\${1:literal}")
    keys = "test" + EX
    wanted = "\n${1:literal}"


class TabStop_EscapingCharsDollars_BeginningOfDefinitionText(_VimTest):
    snippets = ("test", "\\${1:literal}")
    keys = "test" + EX
    wanted = "${1:literal}"


class TabStop_EscapingChars_Backslash(_VimTest):
    snippets = ("test", r"This \ is a backslash!")
    keys = "test" + EX
    wanted = "This \\ is a backslash!"


class TabStop_EscapingChars_Backslash2(_VimTest):
    snippets = ("test", r"This is a backslash \\ done")
    keys = "test" + EX
    wanted = r"This is a backslash \ done"


class TabStop_EscapingChars_Backslash3(_VimTest):
    snippets = ("test", r"These are two backslashes \\\\ done")
    keys = "test" + EX
    wanted = r"These are two backslashes \\ done"


class TabStop_EscapingChars_Backslash4(_VimTest):
    # Test for bug 746446
    snippets = ("test", r"\\$1{$2}")
    keys = "test" + EX + "hello" + JF + "world"
    wanted = r"\hello{world}"


class TabStop_EscapingChars_RealLife(_VimTest):
    snippets = ("test", r"usage: \`basename \$0\` ${1:args}")
    keys = "test" + EX + "[ -u -v -d ]"
    wanted = "usage: `basename $0` [ -u -v -d ]"


class TabStopEscapingWhenSelected_ECR(_VimTest):
    snippets = ("test", "snip ${1:default}")
    keys = "test" + EX + ESC + "0ihi"
    wanted = "hisnip default"


class TabStopEscapingWhenSelectedSingleCharTS_ECR(_VimTest):
    snippets = ("test", "snip ${1:i}")
    keys = "test" + EX + ESC + "0ihi"
    wanted = "hisnip i"


class TabStopEscapingWhenSelectedNoCharTS_ECR(_VimTest):
    snippets = ("test", "snip $1")
    keys = "test" + EX + ESC + "0ihi"
    wanted = "hisnip "


class TabStopWithOneChar_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "nothing ${1:i} hups")
    keys = "hallo" + EX + "ship"
    wanted = "nothing ship hups"


class TabStopTestJumping_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte ${1:Beginning}")
    keys = "hallo" + EX + JF + "Test" + JF + "Hi"
    wanted = "hallo Test mitte BeginningHi"


class TabStopTestJumping2_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = "hallo" + EX + JF + "Test" + JF + "Hi"
    wanted = "hallo Test Hi"


class TabStopTestJumpingRLExampleWithZeroTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "each_byte { |${1:byte}| $0 }")
    keys = "test" + EX + JF + "Blah"
    wanted = "each_byte { |byte| Blah }"


class TabStopTestJumpingDontJumpToEndIfThereIsTabZero_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    keys = "hallo" + EX + "Test" + JF + "Hi" + JF + JF + "du"
    wanted = "hallo Hi" + 2 * JF + "du Test"


class TabStopTestBackwardJumping_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte${1:Beginning}")
    keys = (
        "hallo"
        + EX
        + "Somelengthy Text"
        + JF
        + "Hi"
        + JB
        + "Lets replace it again"
        + JF
        + "Blah"
        + JF
        + JB * 2
        + JF
    )
    wanted = "hallo Blah mitteLets replace it again" + JB * 2 + JF


class TabStopTestBackwardJumping2_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = (
        "hallo"
        + EX
        + "Somelengthy Text"
        + JF
        + "Hi"
        + JB
        + "Lets replace it again"
        + JF
        + "Blah"
        + JF
        + JB * 2
        + JF
    )
    wanted = "hallo Blah Lets replace it again" + JB * 2 + JF


class TabStopTestMultilineExpand_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0\nnice $1 work\n$3 $2\nSeem to work")
    keys = (
        "test hallo World"
        + ESC
        + "02f i"
        + EX
        + "world"
        + JF
        + "try"
        + JF
        + "test"
        + JF
        + "one more"
        + JF
    )
    wanted = (
        "test hallo one more" + JF + "\nnice world work\n"
        "test try\nSeem to work World"
    )


class TabStop_TSInDefaultTextRLExample_OverwriteNone_ECR(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX
    wanted = """<div id="some_id">\n  \n</div>"""


class TabStop_TSInDefaultTextRLExample_OverwriteFirst_NoJumpBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + " blah" + JF + "Hallo"
    wanted = """<div blah>\n  Hallo\n</div>"""


class TabStop_TSInDefaultTextRLExample_DeleteFirst(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + BS + JF + "Hallo"
    wanted = """<div>\n  Hallo\n</div>"""


class TabStop_TSInDefaultTextRLExample_OverwriteFirstJumpBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3  $0\n</div>""")
    keys = (
        "test"
        + EX
        + "Hi"
        + JF
        + "Hallo"
        + JB
        + "SomethingElse"
        + JF
        + "Nupl"
        + JF
        + "Nox"
    )
    wanted = """<divSomethingElse>\n  Nupl  Nox\n</div>"""


class TabStop_TSInDefaultTextRLExample_OverwriteSecond(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End"
    wanted = """<div id="no">\n  End\n</div>"""


class TabStop_TSInDefaultTextRLExample_OverwriteSecondTabBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3 $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End" + JB + "yes" + JF + "Begin" + JF + "Hi"
    wanted = """<div id="yes">\n  Begin Hi\n</div>"""


class TabStop_TSInDefaultTextRLExample_OverwriteSecondTabBackTwice(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3 $0\n</div>""")
    keys = (
        "test"
        + EX
        + JF
        + "no"
        + JF
        + "End"
        + JB
        + "yes"
        + JB
        + " allaway"
        + JF
        + "Third"
        + JF
        + "Last"
    )
    wanted = """<div allaway>\n  Third Last\n</div>"""


class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecond(_VimTest):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "ups" + JF + "End"
    wanted = """haupsblEnd"""


class TabStop_TSInDefaultText_ZeroLengthZerothTabstop(_VimTest):
    snippets = (
        "test",
        """Test: ${1:snippet start\nNested tabstop: $0\nsnippet end}\nTrailing text""",
    )
    keys = "test" + EX + JF + "hello"
    wanted = "Test: snippet start\nNested tabstop: hello\nsnippet end\nTrailing text"


class TabStop_TSInDefaultText_ZeroLengthZerothTabstop_Override(_VimTest):
    snippets = (
        "test",
        """Test: ${1:snippet start\nNested tabstop: $0\nsnippet end}\nTrailing text""",
    )
    keys = "test" + EX + "blub" + JF + "hello"
    wanted = "Test: blub\nTrailing texthello"


class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteFirst(_VimTest):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + "ups" + JF + "End"
    wanted = """hupslEnd"""


class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecondJumpBackOverwrite(
    _VimTest
):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "longertext" + JB + "overwrite" + JF + "End"
    wanted = """hoverwritelEnd"""


class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecondJumpBackAndForward0(
    _VimTest
):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "longertext" + JB + JF + "overwrite" + JF + "End"
    wanted = """haoverwriteblEnd"""


class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecondJumpBackAndForward1(
    _VimTest
):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "longertext" + JB + JF + JF + "End"
    wanted = """halongertextblEnd"""


class TabStop_TSInDefaultNested_OverwriteOneJumpBackToOther(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second ${3:third}}} $4")
    keys = "test" + EX + JF + "Hallo" + JF + "Ende"
    wanted = "hi this Hallo Ende"


class TabStop_TSInDefaultNested_OverwriteOneJumpToThird(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second ${3:third}}} $4")
    keys = "test" + EX + JF + JF + "Hallo" + JF + "Ende"
    wanted = "hi this second Hallo Ende"


class TabStop_TSInDefaultNested_OverwriteOneJumpAround(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second ${3:third}}} $4")
    keys = "test" + EX + JF + JF + "Hallo" + JB + JB + "Blah" + JF + "Ende"
    wanted = "hi Blah Ende"


class TabStop_TSInDefault_MirrorsOutside_DoNothing(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX
    wanted = "hi this second second"


class TabStop_TSInDefault_MirrorsOutside_OverwriteSecond(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX + JF + "Hallo"
    wanted = "hi this Hallo Hallo"


class TabStop_TSInDefault_MirrorsOutside_Overwrite0(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX + "Hallo"
    wanted = "hi Hallo "


class TabStop_TSInDefault_MirrorsOutside_Overwrite1(_VimTest):
    snippets = ("test", "$1: ${1:'${2:second}'} $2")
    keys = "test" + EX + "Hallo"
    wanted = "Hallo: Hallo "


class TabStop_TSInDefault_MirrorsOutside_OverwriteSecond1(_VimTest):
    snippets = ("test", "$1: ${1:'${2:second}'} $2")
    keys = "test" + EX + JF + "Hallo"
    wanted = "'Hallo': 'Hallo' Hallo"


class TabStop_TSInDefault_MirrorsOutside_OverwriteFirstSwitchNumbers(_VimTest):
    snippets = ("test", "$2: ${2:'${1:second}'} $1")
    keys = "test" + EX + "Hallo"
    wanted = "'Hallo': 'Hallo' Hallo"


class TabStop_TSInDefault_MirrorsOutside_OverwriteFirst_RLExample(_VimTest):
    snippets = (
        "test",
        """`!p snip.rv = t[1].split('/')[-1].lower().strip("'")` = require(${1:'${2:sys}'})""",
    )
    keys = "test" + EX + "WORLD" + JF + "End"
    wanted = "world = require(WORLD)End"


class TabStop_TSInDefault_MirrorsOutside_OverwriteSecond_RLExample(_VimTest):
    snippets = (
        "test",
        """`!p snip.rv = t[1].split('/')[-1].lower().strip("'")` = require(${1:'${2:sys}'})""",
    )
    keys = "test" + EX + JF + "WORLD" + JF + "End"
    wanted = "world = require('WORLD')End"


class TabStop_Multiline_Leave(_VimTest):
    snippets = ("test", "hi ${1:first line\nsecond line} world")
    keys = "test" + EX
    wanted = "hi first line\nsecond line world"


class TabStop_Multiline_Overwrite(_VimTest):
    snippets = ("test", "hi ${1:first line\nsecond line} world")
    keys = "test" + EX + "Nothing"
    wanted = "hi Nothing world"


class TabStop_Multiline_MirrorInFront_Leave(_VimTest):
    snippets = ("test", "hi $1 ${1:first line\nsecond line} world")
    keys = "test" + EX
    wanted = "hi first line\nsecond line first line\nsecond line world"


class TabStop_Multiline_MirrorInFront_Overwrite(_VimTest):
    snippets = ("test", "hi $1 ${1:first line\nsecond line} world")
    keys = "test" + EX + "Nothing"
    wanted = "hi Nothing Nothing world"


class TabStop_Multiline_DelFirstOverwriteSecond_Overwrite(_VimTest):
    snippets = ("test", "hi $1 $2 ${1:first line\nsecond line} ${2:Hi} world")
    keys = "test" + EX + BS + JF + "Nothing"
    wanted = "hi  Nothing  Nothing world"


class TabStopNavigatingInInsertModeSimple_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo ${1:WELT} ups")
    keys = "hallo" + EX + "haselnut" + 2 * ARR_L + "hips" + JF + "end"
    wanted = "Hallo haselnhipsut upsend"


class TabStop_CROnlyOnSelectedNear(_VimTest):
    snippets = ("test", "t$1t${2: }t{\n\t$0\n}")
    keys = "test" + EX + JF + "\n" + JF + "t"
    wanted = "tt\nt{\n\tt\n}"


class TabStop_AdjacentTabStopAddText_ExpectCorrectResult(_VimTest):
    snippets = ("test", "[ $1$2 ] $1")
    keys = "test" + EX + "Hello" + JF + "World" + JF
    wanted = "[ HelloWorld ] Hello"


class TabStop_KeepCorrectJumpListOnOverwriteOfPartOfSnippet(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet i
        ia$1: $2
        endsnippet

        snippet ia
        ia($1, $2)
        endsnippet"""
    }
    keys = "i" + EX + EX + "1" + JF + "2" + JF + " after" + JF + "3"
    wanted = "ia(1, 2) after: 3"


class TabStop_KeepCorrectJumpListOnOverwriteOfPartOfSnippetRE(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet i
        ia$1: $2
        endsnippet

        snippet "^ia" "regexp" r
        ia($1, $2)
        endsnippet"""
    }
    keys = "i" + EX + EX + "1" + JF + "2" + JF + " after" + JF + "3"
    wanted = "ia(1, 2) after: 3"
