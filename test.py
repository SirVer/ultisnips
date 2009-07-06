#!/usr/bin/env python
# encoding: utf-8
#

import os
import tempfile
import unittest
import time

# Some constants for better reading
BS = '\x7f'
ESC = '\x1b'
ARR_L = '\x1bOD'
ARR_R = '\x1bOC'
ARR_U = '\x1bOA'
ARR_D = '\x1bOB'

def send(s,session):
        os.system("screen -x %s -X stuff '%s'" % (session,s))

def type(str, session):
    """
    Send the keystrokes to vim via screen. Pause after each char, so
    vim can handle this
    """
    for c in str:
        send(c, session)

class _VimTest(unittest.TestCase):
    snippets = ("dummy", "donotdefine")
    text_before = " --- some text before --- "
    text_after =  " --- some text after --- "
    wanted = ""
    keys = ""

    def send(self,s):
        send(s, self.session)

    def type(self,s):
        type(s, self.session)

    def check_output(self):
        wanted = self.text_before + '\n\n' + self.wanted + \
                '\n\n' + self.text_after
        self.assertEqual(self.output, wanted)

    def runTest(self): self.check_output()

    def setUp(self):
        self.send(ESC)

        self.send(":py PySnipSnippets.reset()\n")

        if not isinstance(self.snippets[0],tuple):
            self.snippets = ( self.snippets, )

        for s in self.snippets:
            sv,content = s[:2]
            descr = ""
            if len(s) == 3:
                descr = s[-1]
            self.send(''':py << EOF
PySnipSnippets.add_snippet("%s","""%s""", "%s")
EOF
''' % (sv,content.encode("string-escape"), descr.encode("string-escape"))
            )

        # Clear the buffer
        self.send("bggVGd")

        if not self.interrupt:
            # Enter insert mode
            self.send("i")

            self.send(self.text_before + '\n\n')
            self.send('\n\n' + self.text_after)

            # Go to the middle of the buffer
            self.send(ESC + "ggjji")

            # Execute the command
            self.type(self.keys)

            handle, fn = tempfile.mkstemp(prefix="PySnipEmuTest",suffix=".txt")
            os.close(handle)
            os.unlink(fn)

            self.send(ESC + ":w! %s\n" % fn)

            # Read the output, chop the trailing newline
            tries = 50
            while tries:
                if os.path.exists(fn):
                    self.output = open(fn,"r").read()[:-1]
                    break
                time.sleep(.05)
                tries -= 1

##################
# Simple Expands #
##################
class _SimpleExpands(_VimTest):
    snippets = ("hallo", "Hallo Welt!")

class SimpleExpand_ExceptCorrectResult(_SimpleExpands):
    keys = "hallo\t"
    wanted = "Hallo Welt!"

class SimpleExpandTypeAfterExpand_ExceptCorrectResult(_SimpleExpands):
    keys = "hallo\tand again"
    wanted = "Hallo Welt!and again"

class SimpleExpandTypeAndDelete_ExceptCorrectResult(_SimpleExpands):
    keys = "na du hallo\tand again\b\b\b\b\bblub"
    wanted = "na du Hallo Welt!and blub"

class DoNotExpandAfterSpace_ExceptCorrectResult(_SimpleExpands):
    keys = "hallo \t"
    wanted = "hallo "

class ExpandInTheMiddleOfLine_ExceptCorrectResult(_SimpleExpands):
    keys = "Wie hallo gehts?" + ESC + "bhi\t"
    wanted = "Wie Hallo Welt! gehts?"
class MultilineExpand_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts?")
    keys = "Wie hallo gehts?" + ESC + "bhi\t"
    wanted = "Wie Hallo Welt!\nUnd Wie gehts? gehts?"
class MultilineExpandTestTyping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts?")
    wanted = "Wie Hallo Welt!\nUnd Wie gehts?Huiui! gehts?"
    keys = "Wie hallo gehts?" + ESC + "bhi\tHuiui!"

############
# TabStops #
############
class TabStopSimpleReplace_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} ${1:Beginning}")
    keys = "hallo\tna\tDu Nase"
    wanted = "hallo Du Nase na"
class TabStopSimpleReplaceSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} a small feed")
    keys = "hallo\tNase"
    wanted = "hallo Nase a small feed"
class TabStopSimpleReplaceSurrounded1_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 a small feed")
    keys = "hallo\tNase"
    wanted = "hallo Nase a small feed"


class ExitTabStop_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "$0 run")
    keys = "echo\ttest"
    wanted = "test run"

class TabStopNoReplace_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "echo ${1:Hallo}")
    keys = "echo\t"
    wanted = "echo Hallo"

# TODO: multiline tabstops, maybe?

class TabStopEscapingWhenSelected_ECR(_VimTest):
    snippets = ("test", "snip ${1:default}")
    keys = "test\t" + ESC + "0ihi"
    wanted = "hisnip default"
class TabStopEscapingWhenSelectedSingleCharTS_ECR(_VimTest):
    snippets = ("test", "snip ${1:i}")
    keys = "test\t" + ESC + "0ihi"
    wanted = "hisnip i"
class TabStopEscapingWhenSelectedNoCharTS_ECR(_VimTest):
    snippets = ("test", "snip $1")
    keys = "test\t" + ESC + "0ihi"
    wanted = "hisnip "

class TabStopUsingBackspaceToDeleteDefaultValue_ECR(_VimTest):
    snippets = ("test", "snip ${1/.+/(?0:matched)/} ${1:default}")
    keys = "test\t" + BS
    wanted = "snip  "
class TabStopUsingBackspaceToDeleteDefaultValueInFirstTab_ECR(_VimTest):
    snippets = ("test", "snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} "
                "${1:default} ${2:def}")
    keys = "test\t" + BS + "\thi"
    wanted = "snip  m2  hi"
class TabStopUsingBackspaceToDeleteDefaultValueInSecondTab_ECR(_VimTest):
    snippets = ("test", "snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} "
                "${1:default} ${2:def}")
    keys = "test\thi\t" + BS
    wanted = "snip m1  hi "
class TabStopUsingBackspaceToDeleteDefaultValueTypeSomethingThen_ECR(_VimTest):
    snippets = ("test", "snip ${1/.+/(?0:matched)/} ${1:default}")
    keys = "test\t" + BS + "hallo"
    wanted = "snip matched hallo"

class TabStopWithOneChar_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "nothing ${1:i} hups")
    keys = "hallo\tship"
    wanted = "nothing ship hups"

class TabStopTestJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte ${1:Beginning}")
    keys = "hallo\t\tTest\tHi"
    wanted = "hallo Test mitte BeginningHi"
class TabStopTestJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = "hallo\t\tTest\tHi"
    wanted = "hallo Test Hi"

class TestJumpingDontJumpToEndIfThereIsTabZero_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    keys = "hallo\tTest\tHi\t\tdu"
    wanted = "hallo Hidu Test"

class TabStopTestBackwardJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte${1:Beginning}")
    keys = "hallo\tSomelengthy Text\tHi+Lets replace it again\tBlah\t++\t"
    wanted = "hallo Blah mitteLets replace it again"
class TabStopTestBackwardJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = "hallo\tSomelengthy Text\tHi+Lets replace it again\tBlah\t++\t"
    wanted = "hallo Blah Lets replace it again"

class TabStopTestMultilineExpand_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0\nnice $1 work\n$3 $2\nSeem to work")
    keys ="test hallo World" + ESC + "02f i\tworld\ttry\ttest\tone more\t\t"
    wanted = "test hallo one more\nnice world work\n" \
            "test try\nSeem to work World"

# TODO: expand, jump forward, jump backwards should all be individual
# functions
# TODO: a dirty bug when escaping when a tabstop is selected. This must be detected
# Multiline text pasting
# Recursive Tabstops: TODO: this will still take some time
# class RecTabStops_SimpleCase_ExceptCorrectResult(_VimTest):
#     snippets = ("m", "[ ${1:first}  ${2:sec} ]")
#     keys = "m\tm\thello\tworld\tend"
#     wanted = "[ [ hello  world ]  end ]"
# class RecTabStops_SimpleCaseLeaveSecond_ExceptCorrectResult(_VimTest):
#     snippets = ("m", "[ ${1:first}  ${2:sec} ]")
#     keys = "m\tm\thello\tworld\t"
#     wanted = "[ [ hello  world ]  sec ]"

# # TODO: pasting with <C-R> while mirroring, also multiline
# ###########
# # MIRRORS #
# ###########
class TextTabStopTextAfterTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 Hinten\n$1")
    keys = "test\thallo"
    wanted = "hallo Hinten\nhallo"
class TextTabStopTextBeforeTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1\n$1")
    keys = "test\thallo"
    wanted = "Vorne hallo\nhallo"
class TextTabStopTextSurroundedTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1 Hinten\n$1")
    keys = "test\thallo test"
    wanted = "Vorne hallo test Hinten\nhallo test"

class TextTabStopTextBeforeMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1")
    keys = "test\thallo"
    wanted = "hallo\nVorne hallo"
class TextTabStopAfterMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1 Hinten")
    keys = "test\thallo"
    wanted = "hallo\nhallo Hinten"
class TextTabStopSurroundMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1 Hinten")
    keys = "test\thallo welt"
    wanted = "hallo welt\nVorne hallo welt Hinten"
class TextTabStopAllSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ObenVorne $1 ObenHinten\nVorne $1 Hinten")
    keys = "test\thallo welt"
    wanted = "ObenVorne hallo welt ObenHinten\nVorne hallo welt Hinten"

class MirrorBeforeTabstopLeave_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test\t"
    wanted = "this is it this is it this is it"
class MirrorBeforeTabstopOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test\ta"
    wanted = "a a a"

class TextTabStopSimpleMirrorMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test\thallo"
    wanted = "hallo\nhallo"
class SimpleMirrorMultilineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "    $1\n$1\na$1b\n$1\ntest $1 mich")
    keys = "test\thallo"
    wanted = "    hallo\nhallo\nahallob\nhallo\ntest hallo mich"
class MultilineTabStopSimpleMirrorMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n\n$1\n\n$1")
    keys = "test\thallo Du\nHi"
    wanted = "hallo Du\nHi\n\nhallo Du\nHi\n\nhallo Du\nHi"
class MultilineTabStopSimpleMirrorMultiline1_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test\thallo Du\nHi"
    wanted = "hallo Du\nHi\nhallo Du\nHi\nhallo Du\nHi"
# TODO: Multiline delete over line endings
class MultilineTabStopSimpleMirrorDeleteInLine_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test\thallo Du\nHi\b\bAch Blah"
    wanted = "hallo Du\nAch Blah\nhallo Du\nAch Blah\nhallo Du\nAch Blah"
class TextTabStopSimpleMirrorMultilineMirrorInFront_ECR(_VimTest):
    snippets = ("test", "$1\n${1:sometext}")
    keys = "test\thallo\nagain"
    wanted = "hallo\nagain\nhallo\nagain"

class SimpleMirrorDelete_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test\thallo\b\b"
    wanted = "hal\nhal"

class SimpleMirrorSameLine_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1")
    keys = "test\thallo"
    wanted = "hallo hallo"
class Transformation_SimpleMirrorSameLineBeforeTabDefVal_ECR(_VimTest):
    snippets = ("test", "$1 ${1:replace me}")
    keys = "test\thallo foo"
    wanted = "hallo foo hallo foo"
class SimpleMirrorSameLineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test\thallo du"
    wanted = "hallo du hallo du hallo du hallo du"
class SimpleMirrorSameLineManyMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test\thallo du\nwie gehts?"
    wanted = "hallo du\nwie gehts? hallo du\nwie gehts? hallo du\nwie gehts?" \
            " hallo du\nwie gehts?"
class SimpleMirrorDeleteSomeEnterSome_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test\thallo\b\bhups"
    wanted = "halhups\nhalhups"


class SimpleTabstopWithDefaultSimpelType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test\tworld"
    wanted = "ha world\nworld"
class SimpleTabstopWithDefaultComplexType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test\tworld"
    wanted = "ha world world\nanother: world mirror"
class SimpleTabstopWithDefaultSimpelKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test\t"
    wanted = "ha defa\ndefa"
class SimpleTabstopWithDefaultComplexKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test\t"
    wanted = "ha default value default value\nanother: default value mirror"

# TODO: Mehrer tabs und mehrere mirrors
class TabstopWithMirrorInDefaultNoType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:blub} ${2:$1.h}")
    keys = "test\t"
    wanted = "ha blub blub.h"
class TabstopWithMirrorInDefaultTwiceAndExtra_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h $1.c}\ntest $1")
    keys = "test\tstdin"
    wanted = "ha stdin stdin.h stdin.c\ntest stdin"
class TabstopWithMirrorInDefaultMultipleLeave_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test\tstdin"
    wanted = "ha stdin snip stdin.h snip"
class TabstopWithMirrorInDefaultMultipleOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test\tstdin\tdo snap"
    wanted = "ha stdin do snap stdin.h do snap"
class TabstopWithMirrorInDefaultOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h}")
    keys = "test\tstdin\toverwritten"
    wanted = "ha stdin overwritten"

class MirrorRealLifeExample_ExceptCorrectResult(_VimTest):
    snippets = (
        ("for", "for(size_t ${2:i} = 0; $2 < ${1:count}; ${3:++$2})" \
         "\n{\n\t${0:/* code */}\n}"),
    )
    keys ="for\t100\tavar\b\b\b\ba_variable\ta_variable *= 2\t// do nothing"
    wanted = """for(size_t a_variable = 0; a_variable < 100; a_variable *= 2)
{
\t// do nothing
}"""


###################
# TRANSFORMATIONS #
###################
class Transformation_SimpleCase_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    keys = "test\thallo foo boy"
    wanted = "hallo foo boy hallo batzl boy"
class Transformation_SimpleCaseNoTransform_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    keys = "test\thallo"
    wanted = "hallo hallo"
class Transformation_SimpleCaseTransformInFront_ExceptCorrectResult(_VimTest):
    snippets = ("test", "${1/foo/batzl/} $1")
    keys = "test\thallo foo"
    wanted = "hallo batzl hallo foo"
class Transformation_SimpleCaseTransformInFrontDefVal_ECR(_VimTest):
    snippets = ("test", "${1/foo/batzl/} ${1:replace me}")
    keys = "test\thallo foo"
    wanted = "hallo batzl hallo foo"
class Transformation_MultipleTransformations_ECR(_VimTest):
    snippets = ("test", "${1:Some Text}${1/.+/\U$0\E/}\n${1/.+/\L$0\E/}")
    keys = "test\tSomE tExt "
    wanted = "SomE tExt SOME TEXT \nsome text "
class Transformation_TabIsAtEndAndDeleted_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    keys = "hallo test\tsome\b\b\b\b\b"
    wanted = "hallo "
class Transformation_TabIsAtEndAndDeleted1_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    keys = "hallo test\tsome\b\b\b\bmore"
    wanted = "hallo is somethingmore"
class Transformation_TabIsAtEndNoTextLeave_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    keys = "hallo test\t"
    wanted = "hallo "
class Transformation_TabIsAtEndNoTextType_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    keys = "hallo test\tb"
    wanted = "hallo is somethingb"


class Transformation_Backreference_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/([ab])oo/$1ull/}")
    keys = "test\tfoo boo aoo"
    wanted = "foo boo aoo foo bull aoo"
class Transformation_BackreferenceTwice_ExceptCorrectResult(_VimTest):
    snippets = ("test", r"$1 ${1/(dead) (par[^ ]*)/this $2 is a bit $1/}")
    keys = "test\tdead parrot"
    wanted = "dead parrot this parrot is a bit dead"

class Transformation_CleverTransformUpercaseChar_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.)/\u$1/}")
    keys = "test\thallo"
    wanted = "hallo Hallo"
class Transformation_CleverTransformLowercaseChar_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\l$1/}")
    keys = "test\tHallo"
    wanted = "Hallo hallo"
class Transformation_CleverTransformLongUpper_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\U$1\E/}")
    keys = "test\thallo"
    wanted = "hallo HALLO"
class Transformation_CleverTransformLongLower_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\L$1\E/}")
    keys = "test\tHALLO"
    wanted = "HALLO hallo"

class Transformation_ConditionalInsertionSimple_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(^a).*/(?0:began with an a)/}")
    keys = "test\ta some more text"
    wanted = "a some more text began with an a"
class Transformation_CIBothDefinedNegative_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    keys = "test\tb some"
    wanted = "b some no"
class Transformation_CIBothDefinedPositive_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    keys = "test\ta some"
    wanted = "a some yes"
class Transformation_ConditionalInsertRWEllipsis_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/(\w+(?:\W+\w+){,7})\W*(.+)?/$1(?2:...)/}")
    keys = "test\ta b  c d e f ghhh h oha"
    wanted = "a b  c d e f ghhh h oha a b  c d e f ghhh h..."

class Transformation_CINewlines_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */\n/}")
    keys = "test\ttest, hallo"
    wanted = "test, hallo test\nhallo"
class Transformation_CIEscapedParensinReplace_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/hal((?:lo)|(?:ul))/(?1:ha\($1\))/}")
    keys = "test\ttest, halul"
    wanted = "test, halul test, ha(ul)"

class Transformation_OptionIgnoreCase_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/test/blah/i}")
    keys = "test\tTEST"
    wanted = "TEST blah"
class Transformation_OptionReplaceGlobal_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */-/g}")
    keys = "test\ta, nice, building"
    wanted = "a, nice, building a-nice-building"
class Transformation_OptionReplaceGlobalMatchInReplace_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */, /g}")
    keys = "test\ta, nice,   building"
    wanted = "a, nice,   building a, nice, building"

# TODO: conditional in conditional, case folding recursive
# TODO: jumping out of snippet in insert mode
#
print "TODO: backspacing when tab is selected"

###################
# CURSOR MOVEMENT #
###################
class CursorMovement_Multiline_ECR(_VimTest):
    snippets = ("test", r"$1 ${1:a tab}")
    keys = "test\tthis is something\nvery nice\nnot?\tmore text"
    wanted = "this is something\nvery nice\nnot? " \
            "this is something\nvery nice\nnot?more text"


# TODO: expandtab and therelikes

######################
# INSERT MODE MOVING #
######################
class IMMoving_CursorsKeys_ECR(_VimTest):
    snippets = ("test", "${1:Some}")
    keys = "test\ttext" + 3*ARR_U + 6*ARR_D
    wanted = "text"
class IMMoving_DoNotAcceptInputWhenMoved_ECR(_VimTest):
    snippets = ("test", r"$1 ${1:a tab}")
    keys = "test\tthis" + ARR_L + "hallo"
    wanted = "this thihallos"
class IMMoving_NoExiting_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:a tab} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i\ttab" + 7*ARR_L + "\thallo"
    wanted = "hello tab hallo tab this"
class IMMoving_NoExitingEventAtEnd_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:a tab} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i\ttab" + "\thallo"
    wanted = "hello tab hallo tab this"
class IMMoving_ExitWhenOutsideRight_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:blub} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i\ttab" + ARR_R + "\thallo"
    wanted = "hello tab blub tab hallothis"
class IMMoving_NotExitingWhenBarelyOutsideLeft_ECR(_VimTest):
    snippets = ("test", r"${1:Hi} ${2:blub}")
    keys = "hello test this" + ESC + "02f i\ttab" + 3*ARR_L + "\thallo"
    wanted = "hello tab hallo this"
class IMMoving_ExitWhenOutsideLeft_ECR(_VimTest):
    snippets = ("test", r"${1:Hi} ${2:blub}")
    keys = "hello test this" + ESC + "02f i\ttab" + 4*ARR_L + "\thallo"
    wanted = "hellohallo tab blub this"
class IMMoving_ExitWhenOutsideAbove_ECR(_VimTest):
    snippets = ("test", "${1:Hi}\n${2:blub}")
    keys = "hello test this" + ESC + "02f i\ttab" + 1*ARR_U + "\t\nhallo"
    wanted = "hallo\nhello tab\nblub this"
class IMMoving_ExitWhenOutsideBelow_ECR(_VimTest):
    snippets = ("test", "${1:Hi}\n${2:blub}")
    keys = "hello test this" + ESC + "02f i\ttab" + 2*ARR_D + "\ttesthallo\n"
    wanted = "hello tab\nblub this\ntesthallo"

####################
# PROPER INDENTING #
####################
class ProperIndenting_SimpleCase_ECR(_VimTest):
    snippets = ("test", "for\n    blah")
    keys = "    test\tHui"
    wanted = "    for\n        blahHui"
class ProperIndenting_SingleLineNoReindenting_ECR(_VimTest):
    snippets = ("test", "hui")
    keys = "    test\tblah"
    wanted = "    huiblah"

######################
# SELECTING MULTIPLE #
######################
class Multiple_SimpleCaseSelectFirst_ECR(_VimTest):
    snippets = ( ("test", "Case1", "This is Case 1"),
                 ("test", "Case2", "This is Case 2") )
    keys = "test\t1\n"
    wanted = "Case1"
class Multiple_SimpleCaseSelectSecond_ECR(_VimTest):
    snippets = ( ("test", "Case1", "This is Case 1"),
                 ("test", "Case2", "This is Case 2") )
    keys = "test\t2\n"
    wanted = "Case2"

###########################################################################
#                               END OF TEST                               #
###########################################################################
if __name__ == '__main__':
    import sys
    import optparse

    def parse_args():
        p = optparse.OptionParser("%prog [OPTIONS] <test case names to run>")

        p.set_defaults(session="vim", interrupt=False, verbose=False)

        p.add_option("-v", "--verbose", dest="verbose", action="store_true",
            help="print name of tests as they are executed")
        p.add_option("-s", "--session", dest="session",  metavar="SESSION",
            help="send commands to screen session SESSION [%default]")
        p.add_option("-i", "--interrupt", dest="interrupt",
            action="store_true",
            help="Stop after defining the snippet. This allows the user" \
             "to interactively test the snippet in vim. You must give exactly" \
            "one test case on the cmdline. The test will always fail."
        )

        o, args = p.parse_args()
        return o, args

    options,selected_tests = parse_args()

    # The next line doesn't work in python 2.3
    test_loader = unittest.TestLoader()
    all_test_suites = test_loader.loadTestsFromModule(__import__("test"))

    # Send some mappings to vim
    send(":inoremap + <C-R>=PyVimSnips_JumpBackwards()<cr>\n", options.session)
    send(":snoremap + <Esc>:call PyVimSnips_JumpBackwards()<cr>\n",
         options.session)


    # Inform all test case which screen session to use
    suite = unittest.TestSuite()
    for s in all_test_suites:
        for test in s:
            test.session = options.session
            test.interrupt = options.interrupt
            if len(selected_tests):
                id = test.id().split('.')[1]
                if not any([ id.startswith(t) for t in selected_tests ]):
                    continue
            suite.addTest(test)


    if options.verbose:
        v = 2
    else:
        v = 1
    res = unittest.TextTestRunner(verbosity=v).run(suite)

