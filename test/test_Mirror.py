from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class TextTabStopTextAfterTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 Hinten\n$1")
    keys = "test" + EX + "hallo"
    wanted = "hallo Hinten\nhallo"


class TextTabStopTextBeforeTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1\n$1")
    keys = "test" + EX + "hallo"
    wanted = "Vorne hallo\nhallo"


class TextTabStopTextSurroundedTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1 Hinten\n$1")
    keys = "test" + EX + "hallo test"
    wanted = "Vorne hallo test Hinten\nhallo test"


class TextTabStopTextBeforeMirror_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nVorne hallo"


class TextTabStopAfterMirror_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1 Hinten")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nhallo Hinten"


class TextTabStopSurroundMirror_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1 Hinten")
    keys = "test" + EX + "hallo welt"
    wanted = "hallo welt\nVorne hallo welt Hinten"


class TextTabStopAllSurrounded_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ObenVorne $1 ObenHinten\nVorne $1 Hinten")
    keys = "test" + EX + "hallo welt"
    wanted = "ObenVorne hallo welt ObenHinten\nVorne hallo welt Hinten"


class MirrorBeforeTabstopLeave_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test" + EX
    wanted = "this is it this is it this is it"


class MirrorBeforeTabstopOverwrite_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test" + EX + "a"
    wanted = "a a a"


class TextTabStopSimpleMirrorMultiline_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nhallo"


class SimpleMirrorMultilineMany_ExpectCorrectResult(_VimTest):
    snippets = ("test", "    $1\n$1\na$1b\n$1\ntest $1 mich")
    keys = "test" + EX + "hallo"
    wanted = "    hallo\nhallo\nahallob\nhallo\ntest hallo mich"


class MultilineTabStopSimpleMirrorMultiline_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n\n$1\n\n$1")
    keys = "test" + EX + "hallo Du\nHi"
    wanted = "hallo Du\nHi\n\nhallo Du\nHi\n\nhallo Du\nHi"


class MultilineTabStopSimpleMirrorMultiline1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test" + EX + "hallo Du\nHi"
    wanted = "hallo Du\nHi\nhallo Du\nHi\nhallo Du\nHi"


class MultilineTabStopSimpleMirrorDeleteInLine_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test" + EX + "hallo Du\nHi\b\bAch Blah"
    wanted = "hallo Du\nAch Blah\nhallo Du\nAch Blah\nhallo Du\nAch Blah"


class TextTabStopSimpleMirrorMultilineMirrorInFront_ECR(_VimTest):
    snippets = ("test", "$1\n${1:sometext}")
    keys = "test" + EX + "hallo\nagain"
    wanted = "hallo\nagain\nhallo\nagain"


class SimpleMirrorDelete_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo\b\b"
    wanted = "hal\nhal"


class SimpleMirrorSameLine_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1")
    keys = "test" + EX + "hallo"
    wanted = "hallo hallo"


class SimpleMirrorSameLineNoSpace_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1$1")
    keys = "test" + EX + "hallo"
    wanted = "hallohallo"


class SimpleMirrorSameLineNoSpaceInsideOther_ExpectCorrectResult(_VimTest):
    snippets = (("test", "$1$1"), ("outer", "$1"))
    keys = "outer" + EX + "test" + EX + "hallo"
    wanted = "hallohallo"


class SimpleMirrorSameLineNoSpaceSpaceAfter_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1$1 ")
    keys = "test" + EX + "hallo"
    wanted = "hallohallo "


class SimpleMirrorSameLineNoSpaceInsideOtherSpaceAfter_ExpectCorrectResult(_VimTest):
    snippets = (("test", "$1$1 "), ("outer", "$1"))
    keys = "outer" + EX + "test" + EX + "hallo"
    wanted = "hallohallo "


class SimpleMirrorSameLine_InText_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1")
    keys = "ups test blah" + ESC + "02f i" + EX + "hallo"
    wanted = "ups hallo hallo blah"


class SimpleMirrorSameLineBeforeTabDefVal_ECR(_VimTest):
    snippets = ("test", "$1 ${1:replace me}")
    keys = "test" + EX + "hallo foo"
    wanted = "hallo foo hallo foo"


class SimpleMirrorSameLineBeforeTabDefVal_DelB4Typing_ECR(_VimTest):
    snippets = ("test", "$1 ${1:replace me}")
    keys = "test" + EX + BS + "hallo foo"
    wanted = "hallo foo hallo foo"


class SimpleMirrorSameLineMany_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test" + EX + "hallo du"
    wanted = "hallo du hallo du hallo du hallo du"


class SimpleMirrorSameLineManyMultiline_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test" + EX + "hallo du\nwie gehts"
    wanted = (
        "hallo du\nwie gehts hallo du\nwie gehts hallo du\nwie gehts"
        " hallo du\nwie gehts"
    )


class SimpleMirrorDeleteSomeEnterSome_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo\b\bhups"
    wanted = "halhups\nhalhups"


class SimpleTabstopWithDefaultSimpelType_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test" + EX + "world"
    wanted = "ha world\nworld"


class SimpleTabstopWithDefaultComplexType_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test" + EX + "world"
    wanted = "ha world world\nanother: world mirror"


class SimpleTabstopWithDefaultSimpelKeep_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test" + EX
    wanted = "ha defa\ndefa"


class SimpleTabstopWithDefaultComplexKeep_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test" + EX
    wanted = "ha default value default value\nanother: default value mirror"


class TabstopWithMirrorManyFromAll_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $5 ${1:blub} $4 $0 ${2:$1.h} $1 $3 ${4:More}")
    keys = (
        "test"
        + EX
        + "hi"
        + JF
        + "hu"
        + JF
        + "hub"
        + JF
        + "hulla"
        + JF
        + "blah"
        + JF
        + "end"
    )
    wanted = "ha blah hi hulla end hu hi hub hulla"


class TabstopWithMirrorInDefaultNoType_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:blub} ${2:$1.h}")
    keys = "test" + EX
    wanted = "ha blub blub.h"


class TabstopWithMirrorInDefaultNoType1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:blub} ${2:$1}")
    keys = "test" + EX
    wanted = "ha blub blub"


class TabstopWithMirrorInDefaultTwiceAndExtra_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h $1.c}\ntest $1")
    keys = "test" + EX + "stdin"
    wanted = "ha stdin stdin.h stdin.c\ntest stdin"


class TabstopWithMirrorInDefaultMultipleLeave_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test" + EX + "stdin"
    wanted = "ha stdin snip stdin.h snip"


class TabstopWithMirrorInDefaultMultipleOverwrite_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test" + EX + "stdin" + JF + "do snap"
    wanted = "ha stdin do snap stdin.h do snap"


class TabstopWithMirrorInDefaultOverwrite_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h}")
    keys = "test" + EX + "stdin" + JF + "overwritten"
    wanted = "ha stdin overwritten"


class TabstopWithMirrorInDefaultOverwrite1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1}")
    keys = "test" + EX + "stdin" + JF + "overwritten"
    wanted = "ha stdin overwritten"


class TabstopWithMirrorInDefaultNoOverwrite1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1}")
    keys = "test" + EX + "stdin" + JF + JF + "end"
    wanted = "ha stdin stdinend"


class MirrorRealLifeExample_ExpectCorrectResult(_VimTest):
    snippets = (
        (
            "for",
            "for(size_t ${2:i} = 0; $2 < ${1:count}; ${3:++$2})"
            "\n{\n\t${0:/* code */}\n}",
        ),
    )
    keys = (
        "for"
        + EX
        + "100"
        + JF
        + "avar\b\b\b\ba_variable"
        + JF
        + "a_variable *= 2"
        + JF
        + "// do nothing"
    )
    wanted = """for(size_t a_variable = 0; a_variable < 100; a_variable *= 2)
{
\t// do nothing
}"""


class Mirror_TestKill_InsertBefore_NoKill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "wihi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch hinoauch_end"


class Mirror_TestKill_InsertAfter_NoKill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "eiab" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch noauchab_end"


class Mirror_TestKill_InsertBeginning_Kill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "wahi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch ahiuch_end"


class Mirror_TestKill_InsertEnd_Kill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "ehihi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch auchih_end"


class Mirror_TestKillTabstop_Kill(_VimTest):
    snippets = "test", "welt${1:welt${2:welt}welt} $2"
    keys = "hallo test" + EX + "elt"
    wanted = "hallo weltelt "
