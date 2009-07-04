#!/usr/bin/env python
# encoding: utf-8
#

import os
import tempfile
import unittest
import time

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
    text_before = " --- some text before --- "
    text_after =  " --- some text after --- "
    
    def send(self,s):
        send(s, self.session)

    def type(self,s):
        type(s, self.session)

    def check_output(self):
        wanted = self.text_before + '\n\n' + self.wanted + \
                '\n\n' + self.text_after
        self.assertEqual(self.output, wanted)

    def escape(self):
        self.type("\x1b")

    def setUp(self):
        self.escape()

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
            self.escape()
            self.send("ggjji")

            # Execute the command
            self.cmd()


            handle, fn = tempfile.mkstemp(prefix="PySnipEmuTest",suffix=".txt")
            os.close(handle)

            self.escape()
            self.send(":w! %s\n" % fn)

            # Give screen a chance to send the cmd and vim to write the file
            time.sleep(.25)

            # Read the output, chop the trailing newline
            self.output = open(fn,"r").read()[:-1]


    def cmd(self):
        """Overwrite these in the children"""
        pass


##################
# Simple Expands #
##################
class _SimpleExpands(_VimTest):
    snippets = ("hallo", "Hallo Welt!")

class SimpleExpand_ExceptCorrectResult(_SimpleExpands):
    wanted = "Hallo Welt!"
    def cmd(self): self.type("hallo\t")
    def runTest(self): self.check_output()

class SimpleExpandTypeAfterExpand_ExceptCorrectResult(_SimpleExpands):
    wanted = "Hallo Welt!and again"
    def cmd(self): self.type("hallo\tand again")
    def runTest(self): self.check_output()

class SimpleExpandTypeAndDelete_ExceptCorrectResult(_SimpleExpands):
    wanted = "na du Hallo Welt!and blub"
    def cmd(self): self.type("na du hallo\tand again\b\b\b\b\bblub")
    def runTest(self): self.check_output()

class DoNotExpandAfterSpace_ExceptCorrectResult(_SimpleExpands):
    wanted = "hallo "
    def cmd(self): self.type("hallo \t")
    def runTest(self): self.check_output()

class ExpandInTheMiddleOfLine_ExceptCorrectResult(_SimpleExpands):
    wanted = "Wie Hallo Welt! gehts?"
    def cmd(self):
        self.type("Wie hallo gehts?")
        self.escape()
        self.type("bhi\t")
    def runTest(self): self.check_output()

class MultilineExpand_ExceptCorrectResult(_VimTest):
    wanted = "Wie Hallo Welt!\nUnd Wie gehts? gehts?"
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts?")
    def cmd(self):
        self.type("Wie hallo gehts?")
        self.escape()
        self.type("bhi\t")
    def runTest(self): self.check_output()
class MultilineExpandTestTyping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts?")
    wanted = "Wie Hallo Welt!\nUnd Wie gehts?Huiui! gehts?"
    def cmd(self):
        self.type("Wie hallo gehts?")
        self.escape()
        self.type("bhi\tHuiui!")
    def runTest(self): self.check_output()

############
# TabStops #
############
class TabStopSimpleReplace_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} ${1:Beginning}")
    wanted = "hallo Du Nase na"
    def cmd(self):
        self.type("hallo\tna\tDu Nase")
    def runTest(self): self.check_output()
class TabStopSimpleReplaceSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} a small feed")
    wanted = "hallo Nase a small feed"
    def cmd(self):
        self.type("hallo\tNase")
    def runTest(self): self.check_output()
class TabStopSimpleReplaceSurrounded1_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 a small feed")
    wanted = "hallo Nase a small feed"
    def cmd(self):
        self.type("hallo\tNase")
    def runTest(self): self.check_output()


class ExitTabStop_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "$0 run")
    wanted = "test run"
    def cmd(self):
        self.type("echo\ttest")
    def runTest(self): self.check_output()

class TabStopNoReplace_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "echo ${1:Hallo}")
    wanted = "echo Hallo"
    def cmd(self):
        self.type("echo\t")
    def runTest(self): self.check_output()

# TODO: multiline tabstops, maybe?

class TabStopWithOneChar_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "nothing ${1:i} hups")
    wanted = "nothing ship hups"
    def cmd(self):
        self.type("hallo\tship")
    def runTest(self): self.check_output()

class TabStopTestJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte ${1:Beginning}")
    wanted = "hallo Test mitte BeginningHi"
    def cmd(self):
        self.type("hallo\t\tTest\tHi")
    def runTest(self): self.check_output()
class TabStopTestJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    wanted = "hallo Test Hi"
    def cmd(self):
        self.type("hallo\t\tTest\tHi")
    def runTest(self): self.check_output()

class TabStopTestBackwardJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} mitte${1:Beginning}")
    wanted = "hallo Blah mitteLets replace it again"
    def cmd(self):
        self.type(
            "hallo\tSomelengthy Text\tHi+Lets replace it again\tBlah\t++\t")
    def runTest(self): self.check_output()
class TabStopTestBackwardJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    wanted = "hallo Blah Lets replace it again"
    def cmd(self):
        self.type(
            "hallo\tSomelengthy Text\tHi+Lets replace it again\tBlah\t++\t")
    def runTest(self): self.check_output()

class TabStopTestMultilineExpand_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0\nnice $1 work\n$3 $2\nSeem to work")
    wanted = "test hallo one more\nnice world work\n" \
            "test try\nSeem to work World"
    def cmd(self):
        self.type("test hallo World")
        self.escape()
        self.type("02f i\t")
        self.type("world\ttry\ttest\tone more\t\t")
    def runTest(self): self.check_output()

# # TODO: pasting with <C-R> while mirroring
# ###########
# # MIRRORS #
# ###########
class TextTabStopTextAfterTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 Hinten\n$1")
    wanted = "hallo Hinten\nhallo"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class TextTabStopTextBeforeTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1\n$1")
    wanted = "Vorne hallo\nhallo"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class TextTabStopTextSurroundedTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1 Hinten\n$1")
    wanted = "Vorne hallo test Hinten\nhallo test"
    def cmd(self):
        self.type("test\thallo test")
    def runTest(self): self.check_output()

class TextTabStopTextBeforeMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1")
    wanted = "hallo\nVorne hallo"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class TextTabStopAfterMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1 Hinten")
    wanted = "hallo\nhallo Hinten"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class TextTabStopSurroundMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1 Hinten")
    wanted = "hallo welt\nVorne hallo welt Hinten"
    def cmd(self):
        self.type("test\thallo welt")
    def runTest(self): self.check_output()
class TextTabStopAllSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ObenVorne $1 ObenHinten\nVorne $1 Hinten")
    wanted = "ObenVorne hallo welt ObenHinten\nVorne hallo welt Hinten"
    def cmd(self):
        self.type("test\thallo welt")
    def runTest(self): self.check_output()

class MirrorBeforeTabstopLeave_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    wanted = "this is it this is it this is it"
    def cmd(self):
        self.type("test\t")
    def runTest(self): self.check_output()
class MirrorBeforeTabstopOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    wanted = "a a a"
    def cmd(self):
        self.type("test\ta")
    def runTest(self): self.check_output()

class TextTabStopSimpleMirrorMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    wanted = "hallo\nhallo"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class SimpleMirrorMultilineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "    $1\n$1\na$1b\n$1\ntest $1 mich")
    wanted = "    hallo\nhallo\nahallob\nhallo\ntest hallo mich"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class MultilineTabStopSimpleMirrorMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n\n$1\n\n$1")
    wanted = "hallo Du\nHi\n\nhallo Du\nHi\n\nhallo Du\nHi"
    def cmd(self):
        self.type("test\thallo Du\nHi")
    def runTest(self): self.check_output()
class MultilineTabStopSimpleMirrorMultiline1_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    wanted = "hallo Du\nHi\nhallo Du\nHi\nhallo Du\nHi"
    def cmd(self):
        self.type("test\thallo Du\nHi")
    def runTest(self): self.check_output()
# TODO: Multiline delete over line endings
class MultilineTabStopSimpleMirrorDeleteInLine_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    wanted = "hallo Du\nAch Blah\nhallo Du\nAch Blah\nhallo Du\nAch Blah"
    def cmd(self):
        self.type("test\thallo Du\nHi\b\bAch Blah")
    def runTest(self): self.check_output()
class TextTabStopSimpleMirrorMultilineMirrorInFront_ECR(_VimTest):
    snippets = ("test", "$1\n${1:sometext}")
    wanted = "hallo\nagain\nhallo\nagain"
    def cmd(self):
        self.type("test\thallo\nagain")
    def runTest(self): self.check_output()

class SimpleMirrorDelete_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    wanted = "hal\nhal"
    def cmd(self):
        self.type("test\thallo")
        self.type("\b\b")

    def runTest(self): self.check_output()

class SimpleMirrorSameLine_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1")
    wanted = "hallo hallo"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class Transformation_SimpleMirrorSameLineBeforeTabDefVal_ECR(_VimTest):
    snippets = ("test", "$1 ${1:replace me}")
    wanted = "hallo foo hallo foo"
    def cmd(self):
        self.type("test\thallo foo")
    def runTest(self): self.check_output()
class SimpleMirrorSameLineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    wanted = "hallo du hallo du hallo du hallo du"
    def cmd(self):
        self.type("test\thallo du")
    def runTest(self): self.check_output()
class SimpleMirrorSameLineManyMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    wanted = "hallo du\nwie gehts? hallo du\nwie gehts? hallo du\nwie gehts?" \
            " hallo du\nwie gehts?"
    def cmd(self):
        self.type("test\thallo du\nwie gehts?")
    def runTest(self): self.check_output()
class SimpleMirrorDeleteSomeEnterSome_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    wanted = "halhups\nhalhups"
    def cmd(self):
        self.type("test\thallo\b\bhups")
    def runTest(self): self.check_output()


class SimpleTabstopWithDefaultSimpelType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    wanted = "ha world\nworld"
    def cmd(self):
        self.type("test\tworld")
    def runTest(self): self.check_output()
class SimpleTabstopWithDefaultComplexType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    wanted = "ha world world\nanother: world mirror"
    def cmd(self):
        self.type("test\tworld")
    def runTest(self): self.check_output()
class SimpleTabstopWithDefaultSimpelKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    wanted = "ha defa\ndefa"
    def cmd(self):
        self.type("test\t")
    def runTest(self): self.check_output()
class SimpleTabstopWithDefaultComplexKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    wanted = "ha default value default value\nanother: default value mirror"
    def cmd(self):
        self.type("test\t")
    def runTest(self): self.check_output()

# TODO: Mehrer tabs und mehrere mirrors
class TabstopWithMirrorInDefaultNoType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:blub} ${2:$1.h}")
    wanted = "ha blub blub.h"
    def cmd(self):
        self.type("test\t")
    def runTest(self): self.check_output()
class TabstopWithMirrorInDefaultTwiceAndExtra_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h $1.c}\ntest $1")
    wanted = "ha stdin stdin.h stdin.c\ntest stdin"
    def cmd(self):
        self.type("test\tstdin")
    def runTest(self): self.check_output()
class TabstopWithMirrorInDefaultMultipleLeave_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    wanted = "ha stdin snip stdin.h snip"
    def cmd(self):
        self.type("test\tstdin")
    def runTest(self): self.check_output()
class TabstopWithMirrorInDefaultMultipleOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    wanted = "ha stdin do snap stdin.h do snap"
    def cmd(self):
        self.type("test\tstdin\tdo snap")
    def runTest(self): self.check_output()
class TabstopWithMirrorInDefaultOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h}")
    wanted = "ha stdin overwritten"
    def cmd(self):
        self.type("test\tstdin\toverwritten")
    def runTest(self): self.check_output()

class MirrorRealLifeExample_ExceptCorrectResult(_VimTest):
    snippets = (
        ("for", "for(size_t ${2:i} = 0; $2 < ${1:count}; ${3:++$2})" \
         "\n{\n\t${0:/* code */}\n}"),
    )
    wanted = """for(size_t a_variable = 0; a_variable < 100; a_variable *= 2)
{
\t// do nothing
}"""
    def cmd(self):
        self.type("for\t100\tavar\b\b\b\ba_variable\ta_variable *= 2"
                  "\t// do nothing")

    def runTest(self): self.check_output()

# TODO: recursive expansion

###################
# TRANSFORMATIONS #
###################
class Transformation_SimpleCase_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    wanted = "hallo foo boy hallo batzl boy"
    def cmd(self):
        self.type("test\thallo foo boy")
    def runTest(self): self.check_output()
class Transformation_SimpleCaseNoTransform_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    wanted = "hallo hallo"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class Transformation_SimpleCaseTransformInFront_ExceptCorrectResult(_VimTest):
    snippets = ("test", "${1/foo/batzl/} $1")
    wanted = "hallo batzl hallo foo"
    def cmd(self):
        self.type("test\thallo foo")
    def runTest(self): self.check_output()
class Transformation_SimpleCaseTransformInFrontDefVal_ECR(_VimTest):
    snippets = ("test", "${1/foo/batzl/} ${1:replace me}")
    wanted = "hallo batzl hallo foo"
    def cmd(self):
        self.type("test\thallo foo")
    def runTest(self): self.check_output()
class Transformation_MultipleTransformations_ECR(_VimTest):
    snippets = ("test", "${1:Some Text}${1/.+/\U$0\E/}\n${1/.+/\L$0\E/}")
    wanted = "SomE tExt SOME TEXT \nsome text "
    def cmd(self):
        self.type("test\tSomE tExt ")
    def runTest(self): self.check_output()
class Transformation_TabIsAtEndAndDeleted_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    wanted = "hallo "
    def cmd(self):
        self.type("hallo test\tsome\b\b\b\b\b")
    def runTest(self): self.check_output()
class Transformation_TabIsAtEndAndDeleted1_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    wanted = "hallo is somethingmore"
    def cmd(self):
        self.type("hallo test\tsome\b\b\b\bmore")
    def runTest(self): self.check_output()
class Transformation_TabIsAtEndNoTextLeave_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    wanted = "hallo "
    def cmd(self):
        self.type("hallo test\t")
    def runTest(self): self.check_output()
class Transformation_TabIsAtEndNoTextType_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    wanted = "hallo is somethingb"
    def cmd(self):
        self.type("hallo test\tb")
    def runTest(self): self.check_output()


class Transformation_Backreference_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/([ab])oo/$1ull/}")
    wanted = "foo boo aoo foo bull aoo"
    def cmd(self):
        self.type("test\tfoo boo aoo")
    def runTest(self): self.check_output()
class Transformation_BackreferenceTwice_ExceptCorrectResult(_VimTest):
    snippets = ("test", r"$1 ${1/(dead) (par[^ ]*)/this $2 is a bit $1/}")
    wanted = "dead parrot this parrot is a bit dead"
    def cmd(self):
        self.type("test\tdead parrot")
    def runTest(self): self.check_output()

class Transformation_CleverTransformUpercaseChar_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.)/\u$1/}")
    wanted = "hallo Hallo"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class Transformation_CleverTransformLowercaseChar_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\l$1/}")
    wanted = "Hallo hallo"
    def cmd(self):
        self.type("test\tHallo")
    def runTest(self): self.check_output()
class Transformation_CleverTransformLongUpper_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\U$1\E/}")
    wanted = "hallo HALLO"
    def cmd(self):
        self.type("test\thallo")
    def runTest(self): self.check_output()
class Transformation_CleverTransformLongLower_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\L$1\E/}")
    wanted = "HALLO hallo"
    def cmd(self):
        self.type("test\tHALLO")
    def runTest(self): self.check_output()

class Transformation_ConditionalInsertionSimple_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(^a).*/(?0:began with an a)/}")
    wanted = "a some more text began with an a"
    def cmd(self):
        self.type("test\ta some more text")
    def runTest(self): self.check_output()
class Transformation_CIBothDefinedNegative_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    wanted = "b some no"
    def cmd(self):
        self.type("test\tb some")
    def runTest(self): self.check_output()
class Transformation_CIBothDefinedPositive_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    wanted = "a some yes"
    def cmd(self):
        self.type("test\ta some")
    def runTest(self): self.check_output()
class Transformation_ConditionalInsertRWEllipsis_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/(\w+(?:\W+\w+){,7})\W*(.+)?/$1(?2:...)/}")
    wanted = "a b  c d e f ghhh h oha a b  c d e f ghhh h..."
    def cmd(self):
        self.type("test\ta b  c d e f ghhh h oha")
    def runTest(self): self.check_output()

class Transformation_CINewlines_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */\n/}")
    wanted = "test, hallo test\nhallo"
    def cmd(self):
        self.type("test\ttest, hallo")
    def runTest(self): self.check_output()

class Transformation_OptionIgnoreCase_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/test/blah/i}")
    wanted = "TEST blah"
    def cmd(self):
        self.type("test\tTEST")
    def runTest(self): self.check_output()
class Transformation_OptionReplaceGlobal_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */-/g}")
    wanted = "a, nice, building a-nice-building"
    def cmd(self):
        self.type("test\ta, nice, building")
    def runTest(self): self.check_output()
class Transformation_OptionReplaceGlobalMatchInReplace_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */, /g}")
    wanted = "a, nice,   building a, nice, building"
    def cmd(self):
        self.type("test\ta, nice,   building")
    def runTest(self): self.check_output()

# TODO: conditional in conditional, case folding recursive
# TODO: jumping out of snippet in insert mode
# 
print "TODO: backspacing when tab is selected"
print "TODO: escape characters '\(' in regular expressions

###################
# CURSOR MOVEMENT #
###################
class CursorMovement_Multiline_ECR(_VimTest):
    snippets = ("test", r"$1 ${1:a tab}")
    wanted = "this is something\nvery nice\nnot? " \
            "this is something\nvery nice\nnot?more text"
    def cmd(self):
        self.type("test\tthis is something\nvery nice\nnot?\t")
        self.type("more text")
    def runTest(self): self.check_output()

# TODO: expandtab and therelikes

####################
# PROPER INDENTING #
####################
class ProperIndenting_SimpleCase_ECR(_VimTest):
    snippets = ("test", "for\n    blah")
    wanted = "    for\n        blahHui"
    def cmd(self):
        self.type("    test\tHui")
    def runTest(self): self.check_output()

######################
# SELECTING MULTIPLE #
######################
class Multiple_SimpleCaseSelectFirst_ECR(_VimTest):
    snippets = ( ("test", "Case1", "This is Case 1"),
                 ("test", "Case2", "This is Case 2") )
    wanted = "Case1"
    def cmd(self):
        self.type("test\t1\n")
    def runTest(self): self.check_output()
class Multiple_SimpleCaseSelectSecond_ECR(_VimTest):
    snippets = ( ("test", "Case1", "This is Case 1"),
                 ("test", "Case2", "This is Case 2") )
    wanted = "Case2"
    def cmd(self):
        self.type("test\t2\n")
    def runTest(self): self.check_output()

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

