#!/usr/bin/env python
# encoding: utf-8
#

import os
import tempfile
import unittest
import time

class _VimTest(unittest.TestCase):
    text_before = " --- some text before --- "
    text_after =  " --- some text after --- "
    def send(self, s):
            os.system("screen -x %s -X stuff '%s'" % (self.session,s))

    def type(self, str):
        """
        Send the keystrokes to vim via screen. Pause after each char, so
        vim can handle this
        """
        for c in str:
            self.send(c)

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

        for sv,content in self.snippets:
            self.send(''':py << EOF
PySnipSnippets.add_snippet("%s","""%s""")
EOF
''' % (sv,content))

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
            time.sleep(.10)

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

class SimpleExpandTypeAfterExpand1_ExceptCorrectResult(_SimpleExpands):
    wanted = "na du Hallo Welt!and again"
    def cmd(self): self.type("na du hallo\tand again")
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

class TabStopTestJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} mitte ${1:Beginning}")
    wanted = "hallo TestHi mitte Beginning"
    def cmd(self):
        self.type("hallo\t\tTest\tHi")
    def runTest(self): self.check_output()
class TabStopTestJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    wanted = "hallo TestHi "
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

# TODO: pasting with <C-R> while mirroring
###########
# MIRRORS #
###########
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
class SimpleMirrorSameLineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1")
    wanted = "hallo du hallo du hallo du hallo du"
    def cmd(self):
        self.type("test\thallo du")
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


# class MirrorMoreInvolved_ExceptCorrectResult(_VimTest):
#     snippets = (
#         ("for", "for(size_t ${2:i} = 0; $2 < ${1:count}; ${3:++$2})\n{\n\t${0:/* code */}\n}"),
#     )
#
#     def cmd(self):
#         self.type("for\t")
#
#     def runTest(self):
#         self.assertEqual(self.output,"hallo Du Nase na")
# TODO: recursive expansion
# TODO: mirrors in default expansion
# TODO: $1 ${1:This is the tabstop}

if __name__ == '__main__':
    import sys
    import optparse

    def parse_args():
        p = optparse.OptionParser("%prog [OPTIONS] <test case names to run>")

        p.set_defaults(session="vim", interrupt=False)

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

    # Inform all test case which screen session to use
    suite = unittest.TestSuite()
    for s in all_test_suites:
        for test in s:
            test.session = options.session
            test.interrupt = options.interrupt
            if len(selected_tests):
                id = test.id().split('.')[1]
                if id not in selected_tests:
                    continue
            suite.addTest(test)


    res = unittest.TextTestRunner().run(suite)

