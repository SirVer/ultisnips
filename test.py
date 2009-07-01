#!/usr/bin/env python
# encoding: utf-8
#

import os
import tempfile
import unittest
import time

class _VimTest(unittest.TestCase):
    def send(self, s):
            os.system("screen -x %s -X stuff '%s'" % (self.session,s))

    def type(self, str):
        """
        Send the keystrokes to vim via screen. Pause after each char, so
        vim can handle this
        """
        for c in str:
            self.send(c)

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

            # Execute the command
            self.cmd()

            handle, fn = tempfile.mkstemp(prefix="PySnipEmuTest",suffix=".txt")
            os.close(handle)

            self.escape()
            self.send(":w! %s\n" % fn)

            # Give screen a chance to send the cmd and vim to write the file
            time.sleep(.01)

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
    def cmd(self):
        self.type("hallo\t")

    def runTest(self):
        self.assertEqual(self.output,"Hallo Welt!")

class SimpleExpandTypeAfterExpand_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.type("hallo\tand again")

    def runTest(self):
        self.assertEqual(self.output,"Hallo Welt!and again")

class SimpleExpandTypeAfterExpand1_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.type("na du hallo\tand again")

    def runTest(self):
        self.assertEqual(self.output,"na du Hallo Welt!and again")

class DoNotExpandAfterSpace_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.type("hallo \t")

    def runTest(self):
        self.assertEqual(self.output,"hallo ")

class ExpandInTheMiddleOfLine_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.type("Wie hallo gehts?")
        self.escape()
        self.type("bhi\t")

    def runTest(self):
        self.assertEqual(self.output,"Wie Hallo Welt! gehts?")

class MultilineExpand_ExceptCorrectResult(_VimTest):
    snippets = (
        ("hallo", "Hallo Welt!\nUnd Wie gehts?"),
    )

    def cmd(self):
        self.type("Wie hallo gehts?")
        self.escape()
        self.type("bhi\t")

    def runTest(self):
        self.assertEqual(self.output, "Wie Hallo Welt!\nUnd Wie gehts? gehts?")

class MultilineExpandTestTyping_ExceptCorrectResult(_VimTest):
    snippets = (
        ("hallo", "Hallo Welt!\nUnd Wie gehts?"),
    )

    def cmd(self):
        self.type("Wie hallo gehts?")
        self.escape()
        self.type("bhi\tHuiui!")

    def runTest(self):
        self.assertEqual(self.output,
             "Wie Hallo Welt!\nUnd Wie gehts?Huiui! gehts?")

############
# TabStops #
############
class TabStopSimpleReplace_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} ${1:Beginning}")
    def cmd(self):
        self.type("hallo\tna\tDu Nase")
    def runTest(self):
        self.assertEqual(self.output,"hallo Du Nase na")

class TabStopSimpleReplaceSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} a small feed")
    def cmd(self):
        self.type("hallo\tNase")
    def runTest(self):
        self.assertEqual(self.output,"hallo Nase a small feed")
class TabStopSimpleReplaceSurrounded1_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 a small feed")
    def cmd(self):
        self.type("hallo\tNase")
    def runTest(self):
        self.assertEqual(self.output,"hallo Nase a small feed")


class ExitTabStop_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "$0 run")
    def cmd(self):
        self.type("echo\ttest")
    def runTest(self):
        self.assertEqual(self.output,"test run")

class TabStopNoReplace_ExceptCorrectResult(_VimTest):
    snippets = ("echo", "echo ${1:Hallo}")
    def cmd(self):
        self.type("echo\t")
    def runTest(self):
        self.assertEqual(self.output,"echo Hallo")

class TabStopTestJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} mitte ${1:Beginning}")
    def cmd(self):
        self.type("hallo\t\tTest\tHi")
    def runTest(self):
        self.assertEqual(self.output,"hallo TestHi mitte Beginning")
class TabStopTestJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    def cmd(self):
        self.type("hallo\t\tTest\tHi")
    def runTest(self):
        self.assertEqual(self.output,"hallo TestHi ")

class TabStopTestBackwardJumping_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} mitte${1:Beginning}")
    def cmd(self):
        self.type("hallo\tSomelengthy Text\tHi+Lets replace it again\tBlah\t++\t")
    def runTest(self):
        self.assertEqual(self.output,"hallo Blah mitteLets replace it again")
class TabStopTestBackwardJumping2_ExceptCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    def cmd(self):
        self.type("hallo\tSomelengthy Text\tHi+Lets replace it again\tBlah\t++\t")
    def runTest(self):
        self.assertEqual(self.output,"hallo Blah Lets replace it again")

# TODO: pasting with <C-R> while mirroring
###########
# MIRRORS #
###########
class TextTabStopTextAfterTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1 Hinten\n$1")
    def cmd(self):
        self.type("test\thallo")
    def runTest(self):
        self.assertEqual(self.output,"hallo Hinten\nhallo")
class TextTabStopTextBeforeTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1\n$1")
    def cmd(self):
        self.type("test\thallo")
    def runTest(self):
        self.assertEqual(self.output,"Vorne hallo\nhallo")
class TextTabStopTextSurroundedTab_ExceptCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1 Hinten\n$1")
    def cmd(self):
        self.type("test\thallo test")
    def runTest(self):
        self.assertEqual(self.output,"Vorne hallo test Hinten\nhallo test")

class TextTabStopTextBeforeMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1")
    def cmd(self):
        self.type("test\thallo")
    def runTest(self):
        self.assertEqual(self.output,"hallo\nVorne hallo")
class TextTabStopAfterMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1 Hinten")
    def cmd(self):
        self.type("test\thallo")
    def runTest(self):
        self.assertEqual(self.output,"hallo\nhallo Hinten")
class TextTabStopSurroundMirror_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1 Hinten")
    def cmd(self):
        self.type("test\thallo welt")
    def runTest(self):
        self.assertEqual(self.output,"hallo welt\nVorne hallo welt Hinten")
class TextTabStopAllSurrounded_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ObenVorne $1 ObenHinten\nVorne $1 Hinten")
    def cmd(self):
        self.type("test\thallo welt")
    def runTest(self):
        self.assertEqual(self.output,"ObenVorne hallo welt ObenHinten\nVorne hallo welt Hinten")


# TODO: mirror mit tabstop mit default variable
# TODO: Mehrer tabs und mehrere mirrors
class TextTabStopSimpleMirrorMultiline_ExceptCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    def cmd(self):
        self.type("test\thallo")
    def runTest(self):
        self.assertEqual(self.output,"hallo\nhallo")
class TextTabStopSimpleMirrorMultilineMany_ExceptCorrectResult(_VimTest):
    snippets = ("test", "    $1\n$1\na$1b\n$1\ntest $1 mich")
    def cmd(self):
        self.type("test\thallo")
    def runTest(self):
        self.assertEqual(self.output,"    hallo\nhallo\nahallob\nhallo\ntest hallo mich")


class TextTabStopSimpleMirrorDelete_ExceptCorrectResult(_VimTest):
    snippets = (
        ("test", "$1\n$1"),
    )
    def cmd(self):
        self.type("test\thallo")
        self.type("\b\b")

    def runTest(self):
        self.assertEqual(self.output,"hal\nhal")

class TextTabStopSimpleMirrorSameLine_ExceptCorrectResult(_VimTest):
    snippets = (
        ("test", "$1 $1"),
    )
    def cmd(self):
        self.type("test\thallo")


    def runTest(self):
        self.assertEqual(self.output,"hallo hallo")
class TextTabStopSimpleMirrorSameLineMany_ExceptCorrectResult(_VimTest):
    snippets = (
        ("test", "$1 $1 $1 $1"),
    )
    def cmd(self):
        self.type("test\thallo du")


    def runTest(self):
        self.assertEqual(self.output,"hallo du hallo du hallo du hallo du")
class TextTabStopSimpleMirrorDeleteSomeEnterSome_ExceptCorrectResult(_VimTest):
    snippets = (
        ("test", "$1\n$1"),
    )
    def cmd(self):
        self.type("test\thallo\b\bhups")

    def runTest(self):
        self.assertEqual(self.output,"halhups\nhalhups")


class TextTabStopSimpleTabstopWithDefaultSimpelType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    def cmd(self):
        self.type("test\tworld")
    def runTest(self):
        self.assertEqual(self.output, "ha world\nworld")
class TextTabStopSimpleTabstopWithDefaultComplexType_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    def cmd(self):
        self.type("test\tworld")
    def runTest(self):
        self.assertEqual(self.output,
            "ha world world\nanother: world mirror")
class TextTabStopSimpleTabstopWithDefaultSimpelKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    def cmd(self):
        self.type("test\t")
    def runTest(self):
        self.assertEqual(self.output, "ha defa\ndefa")
class TextTabStopSimpleTabstopWithDefaultComplexKeep_ExceptCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    def cmd(self):
        self.type("test\t")
    def runTest(self):
        self.assertEqual(self.output,
            "ha default value default value\nanother: default value mirror")



# class TextTabStopMirrorMoreInvolved_ExceptCorrectResult(_VimTest):
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
    all_test_suites = unittest.TestLoader().loadTestsFromModule(__import__("test"))

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

