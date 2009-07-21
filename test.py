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

# Defined Constants
JF = "?" # Jump forwards
JB = "+" # Jump backwards
EX = "\t" # EXPAND

# Some VIM functions
COMPL_KW = chr(24)+chr(14)
COMPL_ACCEPT = chr(25)

def send(s,session):
    os.system("screen -x %s -X stuff '%s'" % (session,s))

def type(str, session, sleeptime):
    """
    Send the keystrokes to vim via screen. Pause after each char, so
    vim can handle this
    """
    for c in str:
        send(c, session)
        time.sleep(sleeptime)

class _VimTest(unittest.TestCase):
    snippets = ("dummy", "donotdefine")
    text_before = " --- some text before --- "
    text_after =  " --- some text after --- "
    wanted = ""
    keys = ""
    sleeptime = 0.03

    def send(self,s):
        send(s, self.session)

    def type(self,s):
        type(s, self.session, self.sleeptime)

    def check_output(self):
        wanted = self.text_before + '\n\n' + self.wanted + \
                '\n\n' + self.text_after
        self.assertEqual(self.output, wanted)

    def runTest(self): self.check_output()

    def _options_on(self):
        pass

    def _options_off(self):
        pass

    def setUp(self):
        self.send(ESC)

        self.send(":py UltiSnips_Manager.reset()\n")

        if not isinstance(self.snippets[0],tuple):
            self.snippets = ( self.snippets, )

        for s in self.snippets:
            sv,content = s[:2]
            descr = ""
            options = ""
            if len(s) > 2:
                descr = s[2]
            if len(s) > 3:
                options = s[3]

            self.send(''':py << EOF
UltiSnips_Manager.add_snippet("%s","""%s""", "%s", "%s")
EOF
''' % (sv,content.encode("string-escape"), descr.encode("string-escape"),
      options
      )
      )

        # Clear the buffer
        self.send("bggVGd")

        if not self.interrupt:
            # Enter insert mode
            self.send("i")

            self.send(self.text_before + '\n\n')
            self.send('\n\n' + self.text_after)

            self.send(ESC)

            # Go to the middle of the buffer
            self.send(ESC + "ggjj")

            self._options_on()

            self.send("i")

            # Execute the command
            self.type(self.keys)

            self.send(ESC)

            self._options_off()

            handle, fn = tempfile.mkstemp(prefix="UltiSnips_Test",suffix=".txt")
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
    keys = "hallo" + EX
    wanted = "Hallo Welt!"
class SimpleExpandTwice_ExceptCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + '\nhallo' + EX
    wanted = "Hallo Welt!\nHallo Welt!"

class SimpleExpandNewLineAndBackspae_ExceptCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + "\nHallo Welt!\n\n\b\b\b\b\b"
    wanted = "Hallo Welt!\nHallo We"
    def _options_on(self):
        self.send(":set backspace=eol,start\n")
    def _options_off(self):
        self.send(":set backspace=\n")

class SimpleExpandTypeAfterExpand_ExceptCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + "and again"
    wanted = "Hallo Welt!and again"

class SimpleExpandTypeAndDelete_ExceptCorrectResult(_SimpleExpands):
    keys = "na du hallo" + EX + "and again\b\b\b\b\bblub"
    wanted = "na du Hallo Welt!and blub"

class DoNotExpandAfterSpace_ExceptCorrectResult(_SimpleExpands):
    keys = "hallo " + EX
    wanted = "hallo "

class ExpandInTheMiddleOfLine_ExceptCorrectResult(_SimpleExpands):
    keys = "Wie hallo gehts" + ESC + "bhi" + EX
    wanted = "Wie Hallo Welt! gehts"
class MultilineExpand_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts")
    keys = "Wie hallo gehts" + ESC + "bhi" + EX
    wanted = "Wie Hallo Welt!\nUnd Wie gehts gehts"
class MultilineExpandTestTyping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts")
    wanted = "Wie Hallo Welt!\nUnd Wie gehtsHuiui! gehts"
    keys = "Wie hallo gehts" + ESC + "bhi" + EX + "Huiui!"

class MultilineExpandWithFormatoptionsOn_ExceptCorrectResult(_VimTest):
    snippets = ("test", "${1:longer expand}\n$0")
    keys = "test" + EX + "This is a longer text that should wrap"
    wanted = "This is a longer\ntext that should\nwrap\n"
    def _options_on(self):
        self.send(":set tw=20\n")
    def _options_off(self):
        self.send(":set tw=0\n")


############
# TabStops #
############
class TabStopSimpleReplace_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} ${1:Beginning}")
    keys = "hallo" + EX + "na" + JF + "Du Nase"
    wanted = "hallo Du Nase na"
class TabStopSimpleReplaceSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} a small feed")
    keys = "hallo" + EX + "Nase"
    wanted = "hallo Nase a small feed"
class TabStopSimpleReplaceSurrounded1_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 a small feed")
    keys = "hallo" + EX + "Nase"
    wanted = "hallo Nase a small feed"
class TabStopSimpleReplaceEndingWithNewline_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt\n")
    keys = "hallo" + EX + "\nAnd more"
    wanted = "Hallo Welt\n\nAnd more"


class ExitTabStop_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "$0 run")
    keys = "echo" + EX + "test"
    wanted = "test run"

class TabStopNoReplace_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "echo ${1:Hallo}")
    keys = "echo" + EX
    wanted = "echo Hallo"

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

class TabStopUsingBackspaceToDeleteDefaultValue_ECR(_VimTest):
    snippets = ("test", "snip ${1/.+/(?0:matched)/} ${1:default}")
    keys = "test" + EX + BS
    wanted = "snip  "
class TabStopUsingBackspaceToDeleteDefaultValueInFirstTab_ECR(_VimTest):
    sleeptime = 0.09 # Do this very slowly
    snippets = ("test", "snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} "
                "${1:default} ${2:def}")
    keys = "test" + EX + BS + JF + "hi"
    wanted = "snip  m2  hi"
class TabStopUsingBackspaceToDeleteDefaultValueInSecondTab_ECR(_VimTest):
    snippets = ("test", "snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} "
                "${1:default} ${2:def}")
    keys = "test" + EX + "hi" + JF + BS
    wanted = "snip m1  hi "
class TabStopUsingBackspaceToDeleteDefaultValueTypeSomethingThen_ECR(_VimTest):
    snippets = ("test", "snip ${1/.+/(?0:matched)/} ${1:default}")
    keys = "test" + EX + BS + "hallo"
    wanted = "snip matched hallo"

class TabStopWithOneChar_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "nothing ${1:i} hups")
    keys = "hallo" + EX + "ship"
    wanted = "nothing ship hups"

class TabStopTestJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte ${1:Beginning}")
    keys = "hallo" + EX + JF + "Test" + JF + "Hi"
    wanted = "hallo Test mitte BeginningHi"
class TabStopTestJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = "hallo" + EX + JF + "Test" + JF + "Hi"
    wanted = "hallo Test Hi"
class TabStopTestJumpingRLExampleWithZeroTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "each_byte { |${1:byte}| $0 }")
    keys = "test" + EX + JF + "Blah"
    wanted = "each_byte { |byte| Blah }"

class TestJumpingDontJumpToEndIfThereIsTabZero_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    keys = "hallo" + EX + "Test" + JF + "Hi" + JF + JF + "du"
    wanted = "hallo Hidu Test"

class TabStopTestBackwardJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte${1:Beginning}")
    keys = "hallo" + EX + "Somelengthy Text" + JF + "Hi" + JB + \
            "Lets replace it again" + JF + "Blah" + JF + JB*2 + JF
    wanted = "hallo Blah mitteLets replace it again"
class TabStopTestBackwardJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = "hallo" + EX + "Somelengthy Text" + JF + "Hi" + JB + \
            "Lets replace it again" + JF + "Blah" + JF + JB*2 + JF
    wanted = "hallo Blah Lets replace it again"

class TabStopTestMultilineExpand_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0\nnice $1 work\n$3 $2\nSeem to work")
    keys ="test hallo World" + ESC + "02f i" + EX + "world" + JF + "try" + \
            JF + "test" + JF + "one more" + JF + JF
    wanted = "test hallo one more\nnice world work\n" \
            "test try\nSeem to work World"

class TabStop_TSInDefaultTextRLExample_OverwriteNone_ECR(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX
    wanted = """<div id="some_id">\n  \n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteFirst(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + " blah" + JF + "Hallo"
    wanted = """<div blah>\n  Hallo\n</div>"""
class TabStop_TSInDefaultTextRLExample_DeleteFirst(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + BS + JF + "Hallo"
    wanted = """<div>\n  Hallo\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteFirstJumpBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3  $0\n</div>""")
    keys = "test" + EX + "Hi" + JF + "Hallo" + JB + "SomethingElse" + JF + \
            "Nupl" + JF + "Nox"
    wanted = """<divSomethingElse>\n  Nupl  Nox\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteSecond(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End"
    wanted = """<div id="no">\n  End\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteSecondTabBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3 $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End" + JB + "yes" + JF + "Begin" \
            + JF + "Hi"
    wanted = """<div id="yes">\n  Begin Hi\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteSecondTabBackTwice(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3 $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End" + JB + "yes" + JB + \
            " allaway" + JF + "Third" + JF + "Last"
    wanted = """<div allaway>\n  Third Last\n</div>"""

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
    keys = "test" + EX + JF + JF + "Hallo" + JB+JB + "Blah" + JF + "Ende"
    wanted = "hi Blah Ende"

class TabStop_TSInDefault_MirrorsOutside_DoNothing(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX
    wanted = "hi this second second"
class TabStop_TSInDefault_MirrorsOutside_OverwriteSecond(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX + JF + "Hallo"
    wanted = "hi this Hallo Hallo"
class TabStop_TSInDefault_MirrorsOutside_Overwrite(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX + "Hallo"
    wanted = "hi Hallo "

class TabStop_Multiline_Leave(_VimTest):
    snippets = ("test", "hi ${1:first line\nsecond line} world" )
    keys = "test" + EX
    wanted = "hi first line\nsecond line world"
class TabStop_Multiline_Overwrite(_VimTest):
    snippets = ("test", "hi ${1:first line\nsecond line} world" )
    keys = "test" + EX + "Nothing"
    wanted = "hi Nothing world"
class TabStop_Multiline_MirrorInFront_Leave(_VimTest):
    snippets = ("test", "hi $1 ${1:first line\nsecond line} world" )
    keys = "test" + EX
    wanted = "hi first line\nsecond line first line\nsecond line world"
class TabStop_Multiline_MirrorInFront_Overwrite(_VimTest):
    snippets = ("test", "hi $1 ${1:first line\nsecond line} world" )
    keys = "test" + EX + "Nothing"
    wanted = "hi Nothing Nothing world"
class TabStop_Multiline_DelFirstOverwriteSecond_Overwrite(_VimTest):
    snippets = ("test", "hi $1 $2 ${1:first line\nsecond line} ${2:Hi} world" )
    keys = "test" + EX + BS + JF + "Nothing"
    wanted = "hi  Nothing  Nothing world"

###########################
# ShellCode Interpolation #
###########################
class TabStop_Shell_SimpleExample(_VimTest):
    snippets = ("test", "hi `echo hallo` you!")
    keys = "test" + EX + "and more"
    wanted = "hi hallo you!and more"
class TabStop_Shell_TextInNextLine(_VimTest):
    snippets = ("test", "hi `echo hallo`\nWeiter")
    keys = "test" + EX + "and more"
    wanted = "hi hallo\nWeiterand more"
class TabStop_Shell_InDefValue_Leave(_VimTest):
    sleeptime = 0.09 # Do this very slowly
    snippets = ("test", "Hallo ${1:now `echo fromecho`} end")
    keys = "test" + EX + JF + "and more"
    wanted = "Hallo now fromecho endand more"
class TabStop_Shell_InDefValue_Overwrite(_VimTest):
    snippets = ("test", "Hallo ${1:now `echo fromecho`} end")
    keys = "test" + EX + "overwrite" + JF + "and more"
    wanted = "Hallo overwrite endand more"

class TabStop_Shell_ShebangPython(_VimTest):
    sleeptime = 0.09 # Do this very slowly
    snippets = ("test", """Hallo ${1:now `#!/usr/bin/env python
print "Hallo Welt"
`} end""")
    keys = "test" + EX + JF + "and more"
    wanted = "Hallo now Hallo Welt endand more"

############################
# PythonCode Interpolation #
############################
class TabStop_PythonCode_SimpleExample(_VimTest):
    snippets = ("test", """hi `!p res = "Hallo"` End""")
    keys = "test" + EX
    wanted = "hi Hallo End"
class TabStop_PythonCode_ReferencePlaceholder(_VimTest):
    snippets = ("test", """${1:hi} `!p res = t[1]+".blah"` End""")
    keys = "test" + EX + "ho"
    wanted = "ho ho.blah End"
class TabStop_PythonCode_ReferencePlaceholderBefore(_VimTest):
    snippets = ("test", """`!p res = len(t[1])*"#"`\n${1:some text}""")
    keys = "test" + EX + "Hallo Welt"
    wanted = "##########\nHallo Welt"
class TabStop_PythonCode_TransformedBeforeMultiLine(_VimTest):
    snippets = ("test", """${1/.+/egal/m} ${1:`!p
res = "Hallo"`} End""")
    keys = "test" + EX
    wanted = "egal Hallo End"

###########################
# VimScript Interpolation #
###########################
class TabStop_VimScriptInterpolation_SimpleExample(_VimTest):
    snippets = ("test", """hi `!v indent(".")` End""")
    keys = "    test" + EX
    wanted = "    hi 4 End"

# TODO: pasting with <C-R> while mirroring, also multiline
# TODO: expandtab and therelikes
# TODO: Multiline text pasting
# TODO: option to avoid snippet expansion when not only indent in front


###############################
# Recursive (Nested) Snippets #
###############################
class RecTabStops_SimpleCase_ExceptCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "m" + EX + "hello" + JF + "world" + JF + "end"
    wanted = "[ [ hello  world ]  end ]"
class RecTabStops_SimpleCaseLeaveSecondSecond_ExceptCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "m" + EX + "hello" + JF + "world" + JF + JF + "end"
    wanted = "[ [ hello  world ]  sec ]end"
class RecTabStops_SimpleCaseLeaveFirstSecond_ExceptCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "m" + EX + "hello" + JF + JF + "world" + JF + "end"
    wanted = "[ [ hello  sec ]  world ]end"

class RecTabStops_InnerWOTabStop_ECR(_VimTest):
    snippets = (
        ("m1", "Just some Text"),
        ("m", "[ ${1:first}  ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + "hi" + JF + "two" + JF + "end"
    wanted = "[ Just some Texthi  two ]end"
class RecTabStops_InnerWOTabStopTwiceDirectly_ECR(_VimTest):
    snippets = (
        ("m1", "JST"),
        ("m", "[ ${1:first}  ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + " m1" + EX + "hi" + JF + "two" + JF + "end"
    wanted = "[ JST JSThi  two ]end"
class RecTabStops_InnerWOTabStopTwice_ECR(_VimTest):
    snippets = (
        ("m1", "JST"),
        ("m", "[ ${1:first}  ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + JF + "m1" + EX + "hi" + JF + "end"
    wanted = "[ JST  JSThi ]end"
class RecTabStops_OuterOnlyWithZeroTS_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "m1" + EX + "CD" + JF + "DE"
    wanted = "A C CD D DE E B"
class RecTabStops_OuterOnlyWithZero_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "m1" + EX + "CD" + JF + "DE"
    wanted = "A C CD D DE E B"
class RecTabStops_ExpandedInZeroTS_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B $1"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "hi" + JF + "m1" + EX + "CD" + JF + "DE"
    wanted = "A C CD D DE E B hi"
class RecTabStops_ExpandedInZeroTSTwice_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B $1"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "hi" + JF + "m" + EX + "again" + JF + "m1" + \
            EX + "CD" + JF + "DE"
    wanted = "A A C CD D DE E B again B hi"
class RecTabStops_ExpandedInZeroTSSecondTimeIgnoreZTS_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B $1"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "hi" + JF + "m" + EX + "m1" + EX + "CD" + JF + "DE"
    wanted = "A A DE B C CD D  E B hi"

class RecTabStops_MirrorInnerSnippet_ECR(_VimTest):
    snippets = (
        ("m", "[ $1 $2 ] $1"),
        ("m1", "ASnip $1 ASnip $2 ASnip"),
    )
    keys = "m" + EX + "m1" + EX + "Hallo" + JF + "Hi" + JF + "two" + JF + "end"
    wanted = "[ ASnip Hallo ASnip Hi ASnip two ] ASnip Hallo ASnip Hi ASnipend"

class RecTabStops_NotAtBeginningOfTS_ExceptCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "hello m" + EX + "hi" + JF + "two" + JF + "three" + \
            JF + "end"
    wanted = "[ hello [ hi  two ]  three ]end"
class RecTabStops_InNewlineInTabstop_ExceptCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "hello\nm" + EX + "hi" + JF + "two" + JF + "three" + \
            JF + "end"
    wanted = "[ hello\n[ hi  two ]  three ]end"
class RecTabStops_InNewlineInTabstopNotAtBeginOfLine_ECR(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "hello\nhello again m" + EX + "hi" + JF + "two" + \
            JF + "three" + JF + "end"
    wanted = "[ hello\nhello again [ hi  two ]  three ]end"

class RecTabStops_InNewlineMultiline_ECR(_VimTest):
    snippets = ("m", "M START\n$0\nM END")
    keys = "m" + EX + "m" + EX
    wanted = "M START\nM START\n\nM END\nM END"
class RecTabStops_InNewlineManualIndent_ECR(_VimTest):
    snippets = ("m", "M START\n$0\nM END")
    keys = "m" + EX + "    m" + EX + "hi"
    wanted = "M START\n    M START\n    hi\n    M END\nM END"
class RecTabStops_InNewlineManualIndentTextInFront_ECR(_VimTest):
    snippets = ("m", "M START\n$0\nM END")
    keys = "m" + EX + "    hallo m" + EX + "hi"
    wanted = "M START\n    hallo M START\n    hi\n    M END\nM END"
class RecTabStops_InNewlineMultilineWithIndent_ECR(_VimTest):
    snippets = ("m", "M START\n    $0\nM END")
    keys = "m" + EX + "m" + EX + "hi"
    wanted = "M START\n    M START\n        hi\n    M END\nM END"
class RecTabStops_InNewlineMultilineWithNonZeroTS_ECR(_VimTest):
    snippets = ("m", "M START\n    $1\nM END -> $0")
    keys = "m" + EX + "m" + EX + "hi" + JF + "hallo"
    wanted = "M START\n    M START\n        hi\n    M END -> \n" \
        "M END -> hallo"

class RecTabStops_BarelyNotLeavingInner_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "a" + 3*ARR_L + JF + "hallo" + \
            JF + "world" + JF + "end"
    wanted = "[ [ a hallo ] world ]end"
class RecTabStops_LeavingInner_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "a" + 4*ARR_L + JF + "hallo" + \
            JF + "world"
    wanted = "[ [ a sec ] hallo ]world"
class RecTabStops_LeavingInnerInner_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "m" + EX + "a" + 4*ARR_L + JF + "hallo" + \
            JF + "world" + JF + "end"
    wanted = "[ [ [ a sec ] hallo ] world ]end"
class RecTabStops_LeavingInnerInnerTwo_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "m" + EX + "a" + 6*ARR_L + JF + "hallo" + \
            JF + "end"
    wanted = "[ [ [ a sec ] sec ] hallo ]end"


class RecTabStops_IgnoreZeroTS_ECR(_VimTest):
    snippets = (
        ("m1", "[ ${1:first} $0 ${2:sec} ]"),
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + "hi" + JF + "two" + \
            JF + "three" + JF + "end"
    wanted = "[ [ hi  two ] three ]end"
class RecTabStops_MirroredZeroTS_ECR(_VimTest):
    snippets = (
        ("m1", "[ ${1:first} ${0:Year, some default text} $0 ${2:sec} ]"),
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + "hi" + JF + "two" + \
            JF + "three" + JF + "end"
    wanted = "[ [ hi   two ] three ]end"



###########
# MIRRORS #
###########
class TextTabStopTextAfterTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 Hinten\n$1")
    keys = "test" + EX + "hallo"
    wanted = "hallo Hinten\nhallo"
class TextTabStopTextBeforeTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1\n$1")
    keys = "test" + EX + "hallo"
    wanted = "Vorne hallo\nhallo"
class TextTabStopTextSurroundedTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1 Hinten\n$1")
    keys = "test" + EX + "hallo test"
    wanted = "Vorne hallo test Hinten\nhallo test"

class TextTabStopTextBeforeMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nVorne hallo"
class TextTabStopAfterMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1 Hinten")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nhallo Hinten"
class TextTabStopSurroundMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1 Hinten")
    keys = "test" + EX + "hallo welt"
    wanted = "hallo welt\nVorne hallo welt Hinten"
class TextTabStopAllSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ObenVorne $1 ObenHinten\nVorne $1 Hinten")
    keys = "test" + EX + "hallo welt"
    wanted = "ObenVorne hallo welt ObenHinten\nVorne hallo welt Hinten"

class MirrorBeforeTabstopLeave_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test" + EX
    wanted = "this is it this is it this is it"
class MirrorBeforeTabstopOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test" + EX + "a"
    wanted = "a a a"

class TextTabStopSimpleMirrorMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nhallo"
class SimpleMirrorMultilineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "    $1\n$1\na$1b\n$1\ntest $1 mich")
    keys = "test" + EX + "hallo"
    wanted = "    hallo\nhallo\nahallob\nhallo\ntest hallo mich"
class MultilineTabStopSimpleMirrorMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n\n$1\n\n$1")
    keys = "test" + EX + "hallo Du\nHi"
    wanted = "hallo Du\nHi\n\nhallo Du\nHi\n\nhallo Du\nHi"
class MultilineTabStopSimpleMirrorMultiline1_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test" + EX + "hallo Du\nHi"
    wanted = "hallo Du\nHi\nhallo Du\nHi\nhallo Du\nHi"
class MultilineTabStopSimpleMirrorDeleteInLine_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test" + EX + "hallo Du\nHi\b\bAch Blah"
    wanted = "hallo Du\nAch Blah\nhallo Du\nAch Blah\nhallo Du\nAch Blah"
class TextTabStopSimpleMirrorMultilineMirrorInFront_ECR(_VimTest):
    snippets = ("test", "$1\n${1:sometext}")
    keys = "test" + EX + "hallo\nagain"
    wanted = "hallo\nagain\nhallo\nagain"

class SimpleMirrorDelete_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo\b\b"
    wanted = "hal\nhal"

class SimpleMirrorSameLine_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1")
    keys = "test" + EX + "hallo"
    wanted = "hallo hallo"
class Transformation_SimpleMirrorSameLineBeforeTabDefVal_ECR(_VimTest):
    snippets = ("test", "$1 ${1:replace me}")
    keys = "test" + EX + "hallo foo"
    wanted = "hallo foo hallo foo"
class SimpleMirrorSameLineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test" + EX + "hallo du"
    wanted = "hallo du hallo du hallo du hallo du"
class SimpleMirrorSameLineManyMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test" + EX + "hallo du\nwie gehts"
    wanted = "hallo du\nwie gehts hallo du\nwie gehts hallo du\nwie gehts" \
            " hallo du\nwie gehts"
class SimpleMirrorDeleteSomeEnterSome_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo\b\bhups"
    wanted = "halhups\nhalhups"


class SimpleTabstopWithDefaultSimpelType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test" + EX + "world"
    wanted = "ha world\nworld"
class SimpleTabstopWithDefaultComplexType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test" + EX + "world"
    wanted = "ha world world\nanother: world mirror"
class SimpleTabstopWithDefaultSimpelKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test" + EX
    wanted = "ha defa\ndefa"
class SimpleTabstopWithDefaultComplexKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test" + EX
    wanted = "ha default value default value\nanother: default value mirror"

class TabstopWithMirrorManyFromAll_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $5 ${1:blub} $4 $0 ${2:$1.h} $1 $3 ${4:More}")
    keys = "test" + EX + "hi" + JF + "hu" + JF + "hub" + JF + "hulla" + \
            JF + "blah" + JF + "end"
    wanted = "ha blah hi hulla end hu hi hub hulla"
class TabstopWithMirrorInDefaultNoType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:blub} ${2:$1.h}")
    keys = "test" + EX
    wanted = "ha blub blub.h"
class TabstopWithMirrorInDefaultTwiceAndExtra_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h $1.c}\ntest $1")
    keys = "test" + EX + "stdin"
    wanted = "ha stdin stdin.h stdin.c\ntest stdin"
class TabstopWithMirrorInDefaultMultipleLeave_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test" + EX + "stdin"
    wanted = "ha stdin snip stdin.h snip"
class TabstopWithMirrorInDefaultMultipleOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test" + EX + "stdin" + JF + "do snap"
    wanted = "ha stdin do snap stdin.h do snap"
class TabstopWithMirrorInDefaultOverwrite_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h}")
    keys = "test" + EX + "stdin" + JF + "overwritten"
    wanted = "ha stdin overwritten"

class MirrorRealLifeExample_ExceptCorrectResult(_VimTest):
    snippets = (
        ("for", "for(size_t ${2:i} = 0; $2 < ${1:count}; ${3:++$2})" \
         "\n{\n" + EX + "${0:/* code */}\n}"),
    )
    keys ="for" + EX + "100" + JF + "avar\b\b\b\ba_variable" + JF + \
            "a_variable *= 2" + JF + "// do nothing"
    wanted = """for(size_t a_variable = 0; a_variable < 100; a_variable *= 2)
{
\t// do nothing
}"""


###################
# TRANSFORMATIONS #
###################
class Transformation_SimpleCase_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    keys = "test" + EX + "hallo foo boy"
    wanted = "hallo foo boy hallo batzl boy"
class Transformation_SimpleCaseNoTransform_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    keys = "test" + EX + "hallo"
    wanted = "hallo hallo"
class Transformation_SimpleCaseTransformInFront_ExceptCorrectResult(_VimTest):
    snippets = ("test", "${1/foo/batzl/} $1")
    keys = "test" + EX + "hallo foo"
    wanted = "hallo batzl hallo foo"
class Transformation_SimpleCaseTransformInFrontDefVal_ECR(_VimTest):
    snippets = ("test", "${1/foo/batzl/} ${1:replace me}")
    keys = "test" + EX + "hallo foo"
    wanted = "hallo batzl hallo foo"
class Transformation_MultipleTransformations_ECR(_VimTest):
    snippets = ("test", "${1:Some Text}${1/.+/\U$0\E/}\n${1/.+/\L$0\E/}")
    keys = "test" + EX + "SomE tExt "
    wanted = "SomE tExt SOME TEXT \nsome text "
class Transformation_TabIsAtEndAndDeleted_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    keys = "hallo test" + EX + "some\b\b\b\b\b"
    wanted = "hallo "
class Transformation_TabIsAtEndAndDeleted1_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    keys = "hallo test" + EX + "some\b\b\b\bmore"
    wanted = "hallo is somethingmore"
class Transformation_TabIsAtEndNoTextLeave_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    keys = "hallo test" + EX
    wanted = "hallo "
class Transformation_TabIsAtEndNoTextType_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    keys = "hallo test" + EX + "b"
    wanted = "hallo is somethingb"
class Transformation_InsideTabLeaveAtDefault_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:${1/.+/(?0:defined $0)/}}")
    keys = "test" + EX + "sometext" + JF
    wanted = "sometext defined sometext"
class Transformation_InsideTabOvertype_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:${1/.+/(?0:defined $0)/}}")
    keys = "test" + EX + "sometext" + JF + "overwrite"
    wanted = "sometext overwrite"


class Transformation_Backreference_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/([ab])oo/$1ull/}")
    keys = "test" + EX + "foo boo aoo"
    wanted = "foo boo aoo foo bull aoo"
class Transformation_BackreferenceTwice_ExceptCorrectResult(_VimTest):
    snippets = ("test", r"$1 ${1/(dead) (par[^ ]*)/this $2 is a bit $1/}")
    keys = "test" + EX + "dead parrot"
    wanted = "dead parrot this parrot is a bit dead"

class Transformation_CleverTransformUpercaseChar_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.)/\u$1/}")
    keys = "test" + EX + "hallo"
    wanted = "hallo Hallo"
class Transformation_CleverTransformLowercaseChar_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\l$1/}")
    keys = "test" + EX + "Hallo"
    wanted = "Hallo hallo"
class Transformation_CleverTransformLongUpper_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\U$1\E/}")
    keys = "test" + EX + "hallo"
    wanted = "hallo HALLO"
class Transformation_CleverTransformLongLower_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\L$1\E/}")
    keys = "test" + EX + "HALLO"
    wanted = "HALLO hallo"

class Transformation_ConditionalInsertionSimple_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(^a).*/(?0:began with an a)/}")
    keys = "test" + EX + "a some more text"
    wanted = "a some more text began with an a"
class Transformation_CIBothDefinedNegative_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    keys = "test" + EX + "b some"
    wanted = "b some no"
class Transformation_CIBothDefinedPositive_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    keys = "test" + EX + "a some"
    wanted = "a some yes"
class Transformation_ConditionalInsertRWEllipsis_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/(\w+(?:\W+\w+){,7})\W*(.+)?/$1(?2:...)/}")
    keys = "test" + EX + "a b  c d e f ghhh h oha"
    wanted = "a b  c d e f ghhh h oha a b  c d e f ghhh h..."
class Transformation_ConditionalInConditional_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/^.*?(-)?(>)?$/(?2::(?1:>:.))/}")
    keys = "test" + EX + "hallo" + ESC + "$a\n" + \
           "test" + EX + "hallo-" + ESC + "$a\n" + \
           "test" + EX + "hallo->"
    wanted = "hallo .\nhallo- >\nhallo-> "

class Transformation_CINewlines_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */\n/}")
    keys = "test" + EX + "test, hallo"
    wanted = "test, hallo test\nhallo"
class Transformation_CIEscapedParensinReplace_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/hal((?:lo)|(?:ul))/(?1:ha\($1\))/}")
    keys = "test" + EX + "test, halul"
    wanted = "test, halul test, ha(ul)"

class Transformation_OptionIgnoreCase_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/test/blah/i}")
    keys = "test" + EX + "TEST"
    wanted = "TEST blah"
class Transformation_OptionReplaceGlobal_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */-/g}")
    keys = "test" + EX + "a, nice, building"
    wanted = "a, nice, building a-nice-building"
class Transformation_OptionReplaceGlobalMatchInReplace_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */, /g}")
    keys = "test" + EX + "a, nice,   building"
    wanted = "a, nice,   building a, nice, building"

###################
# CURSOR MOVEMENT #
###################
class CursorMovement_Multiline_ECR(_VimTest):
    snippets = ("test", r"$1 ${1:a tab}")
    keys = "test" + EX + "this is something\nvery nice\nnot" + JF + "more text"
    wanted = "this is something\nvery nice\nnot " \
            "this is something\nvery nice\nnotmore text"


######################
# INSERT MODE MOVING #
######################
class IMMoving_CursorsKeys_ECR(_VimTest):
    snippets = ("test", "${1:Some}")
    keys = "test" + EX + "text" + 3*ARR_U + 6*ARR_D
    wanted = "text"
class IMMoving_DoNotAcceptInputWhenMoved_ECR(_VimTest):
    snippets = ("test", r"$1 ${1:a tab}")
    keys = "test" + EX + "this" + ARR_L + "hallo"
    wanted = "this thihallos"
class IMMoving_NoExiting_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:a tab} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 7*ARR_L + \
            JF + "hallo"
    wanted = "hello tab hallo tab this"
class IMMoving_NoExitingEventAtEnd_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:a tab} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + JF + "hallo"
    wanted = "hello tab hallo tab this"
class IMMoving_ExitWhenOutsideRight_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:blub} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + ARR_R + JF + "hallo"
    wanted = "hello tab blub tab hallothis"
class IMMoving_NotExitingWhenBarelyOutsideLeft_ECR(_VimTest):
    snippets = ("test", r"${1:Hi} ${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 3*ARR_L + \
            JF + "hallo"
    wanted = "hello tab hallo this"
class IMMoving_ExitWhenOutsideLeft_ECR(_VimTest):
    snippets = ("test", r"${1:Hi} ${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 4*ARR_L + \
            JF + "hallo"
    wanted = "hellohallo tab blub this"
class IMMoving_ExitWhenOutsideAbove_ECR(_VimTest):
    snippets = ("test", "${1:Hi}\n${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 1*ARR_U + JF + \
            "\nhallo"
    wanted = "hallo\nhello tab\nblub this"
class IMMoving_ExitWhenOutsideBelow_ECR(_VimTest):
    snippets = ("test", "${1:Hi}\n${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 2*ARR_D + JF + \
            "testhallo\n"
    wanted = "hello tab\nblub this\ntesthallo"


####################
# PROPER INDENTING #
####################
class ProperIndenting_SimpleCase_ECR(_VimTest):
    snippets = ("test", "for\n    blah")
    keys = "    test" + EX + "Hui"
    wanted = "    for\n        blahHui"
class ProperIndenting_SingleLineNoReindenting_ECR(_VimTest):
    snippets = ("test", "hui")
    keys = "    test" + EX + "blah"
    wanted = "    huiblah"
class ProperIndenting_AutoIndentAndNewline_ECR(_VimTest):
    snippets = ("test", "hui")
    keys = "    test" + EX + "\n"+ "blah"
    wanted = "    hui\n    blah"
    def _options_on(self):
        self.send(":set autoindent\n")
    def _options_off(self):
        self.send(":set noautoindent\n")
        _VimTest.tearDown(self)

####################
# COMPLETION TESTS #
####################
class Completion_SimpleExample_ECR(_VimTest):
    snippets = ("test", "$1 ${1:blah}")
    keys = "superkallifragilistik\ntest" + EX + "sup" + COMPL_KW + \
            COMPL_ACCEPT + " some more"
    wanted = "superkallifragilistik\nsuperkallifragilistik some more " \
            "superkallifragilistik some more"


###################
# SNIPPET OPTIONS #
###################
class SnippetOptions_OverwriteExisting_ECR(_VimTest):
    snippets = (
     ("test", "${1:Hallo}", "Types Hallo"),
     ("test", "${1:World}", "Types World"),
     ("test", "We overwrite", "Overwrite the two", "!"),
    )
    keys = "test" + EX
    wanted = "We overwrite"
class SnippetOptions_OverwriteTwice_ECR(_VimTest):
    snippets = (
        ("test", "${1:Hallo}", "Types Hallo"),
        ("test", "${1:World}", "Types World"),
        ("test", "We overwrite", "Overwrite the two", "!"),
        ("test", "again", "Overwrite again", "!"),
    )
    keys = "test" + EX
    wanted = "again"
class SnippetOptions_OverwriteThenChoose_ECR(_VimTest):
    snippets = (
        ("test", "${1:Hallo}", "Types Hallo"),
        ("test", "${1:World}", "Types World"),
        ("test", "We overwrite", "Overwrite the two", "!"),
        ("test", "No overwrite", "Not overwritten", ""),
    )
    keys = "test" + EX + "1\n\n" + "test" + EX + "2\n"
    wanted = "We overwrite\nNo overwrite"
class SnippetOptions_OnlyExpandWhenWSInFront_Expand(_VimTest):
    snippets = ("test", "Expand me!", "", "b")
    keys = "test" + EX
    wanted = "Expand me!"
class SnippetOptions_OnlyExpandWhenWSInFront_Expand2(_VimTest):
    snippets = ("test", "Expand me!", "", "b")
    keys = "   test" + EX
    wanted = "   Expand me!"
class SnippetOptions_OnlyExpandWhenWSInFront_DontExpand(_VimTest):
    snippets = ("test", "Expand me!", "", "b")
    keys = "a test" + EX
    wanted = "a test"
class SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWO(_VimTest):
    snippets = (
        ("test", "Expand me!", "", "b"),
        ("test", "not at beginning", "", ""),
    )
    keys = "a test" + EX
    wanted = "a not at beginning"
class SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWOChoose(_VimTest):
    snippets = (
        ("test", "Expand me!", "", "b"),
        ("test", "not at beginning", "", ""),
    )
    keys = "  test" + EX + "1\n"
    wanted = "  Expand me!"

######################
# SELECTING MULTIPLE #
######################
class Multiple_SimpleCaseSelectFirst_ECR(_VimTest):
    snippets = ( ("test", "Case1", "This is Case 1"),
                 ("test", "Case2", "This is Case 2") )
    keys = "test" + EX + "1\n"
    wanted = "Case1"
class Multiple_SimpleCaseSelectSecond_ECR(_VimTest):
    snippets = ( ("test", "Case1", "This is Case 1"),
                 ("test", "Case2", "This is Case 2") )
    keys = "test" + EX + "2\n"
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

    # Set the options
    send(""":let g:UltiSnipsExpandTrigger="<tab>"\n""", options.session)
    send(""":let g:UltiSnipsJumpForwardTrigger="?"\n""", options.session)
    send(""":let g:UltiSnipsJumpBackwardTrigger="+"\n""", options.session)

    # Now, source our runtime
    send(":so plugin/UltiSnips.vim\n", options.session)

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

