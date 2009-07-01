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

        # splits = str.split('\t')
        # for w in splits[:-1]:
        #     _send(w + '\t')
        # _send(splits[-1])


    def escape(self):
        self.type("\x1b")

    def setUp(self):
        self.escape()

        self.send(":py PySnipSnippets.reset()\n")

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
    snippets = (
        ("hallo", "Hallo Welt!"),
    )

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
class ExitTabStop_ExceptCorrectResult(_VimTest):
    snippets = (
        ("echo", "$0 run"),
    )

    def cmd(self):
        self.type("echo\ttest")

    def runTest(self):
        self.assertEqual(self.output,"test run")

class TextTabStopNoReplace_ExceptCorrectResult(_VimTest):
    snippets = (
        ("echo", "echo ${1:Hallo}"),
    )

    def cmd(self):
        self.type("echo\t")

    def runTest(self):
        self.assertEqual(self.output,"echo Hallo")

class TextTabStopSimpleReplace_ExceptCorrectResult(_VimTest):
    snippets = (
        ("hallo", "hallo ${0:End} ${1:Beginning}"),
    )

    def cmd(self):
        self.type("hallo\tna\tDu Nase")

    def runTest(self):
        self.assertEqual(self.output,"hallo Du Nase na")

class TextTabStopSimpleReplace_ExceptCorrectResult(_VimTest):
    snippets = (
        ("hallo", "hallo ${0:End} ${1:Beginning}"),
    )

    def cmd(self):
        self.type("hallo\tna\tDu Nase")

    def runTest(self):
        self.assertEqual(self.output,"hallo Du Nase na")

# TODO: multiline mirrors

class TextTabStopSimpleMirror_ExceptCorrectResult(_VimTest):
    snippets = (
        ("test", "$1\n$1"),
    )
    def cmd(self):
        self.type("test\thallo")

    def runTest(self):
        self.assertEqual(self.output,"hallo\nhallo")

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
        ("test", "$1  $1"),
    )
    def cmd(self):
        self.type("test\thallo")


    def runTest(self):
        self.assertEqual(self.output,"hallo  hallo")

class TextTabStopSimpleMirrorDeleteSomeEnterSome_ExceptCorrectResult(_VimTest):
    snippets = (
        ("test", "$1\n$1"),
    )
    def cmd(self):
        self.type("test\thallo\b\bhups")

    def runTest(self):
        self.assertEqual(self.output,"halhups\nhalhups")

# TODO: this is not yet finished
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

