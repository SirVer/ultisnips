#!/usr/bin/env python
# encoding: utf-8
#

import os
import tempfile
import unittest
import time

class _VimTest(unittest.TestCase):
    def type(self, str):
        """
        Send the keystrokes to vim via screen. Pause after each tab, so
        expansion can take place
        """
        def _send(s):
            os.system("screen -X stuff '%s'" % s)

        splits = str.split('\t')
        for w in splits[:-1]:
            _send(w + '\t')
        _send(splits[-1])


    def escape(self):
        self.type("\x1b")

    def setUp(self):
        self.escape()

        self.type(":py PySnipSnippets.reset()\n")

        for sv,content in self.snippets:
            self.type(''':py << EOF
PySnipSnippets.add_snippet("%s","""%s""")
EOF
''' % (sv,content))

        # Clear the buffer
        self.type("bggVGd")

        # Enter insert mode
        self.type("i")

        # Execute the command
        self.cmd()

        handle, fn = tempfile.mkstemp(prefix="PySnipEmuTest",suffix=".txt")
        os.close(handle)

        self.escape()
        self.type(":w! %s\n" % fn)

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

if __name__ == '__main__':
    import sys

    tests = [
        SimpleExpand_ExceptCorrectResult(),
        SimpleExpandTypeAfterExpand_ExceptCorrectResult(),
        SimpleExpandTypeAfterExpand1_ExceptCorrectResult(),
        DoNotExpandAfterSpace_ExceptCorrectResult(),
        ExpandInTheMiddleOfLine_ExceptCorrectResult(),
        MultilineExpand_ExceptCorrectResult(),
        MultilineExpandTestTyping_ExceptCorrectResult(),
        ExitTabStop_ExceptCorrectResult(),
        TextTabStopNoReplace_ExceptCorrectResult(),
        TextTabStopSimpleReplace_ExceptCorrectResult(),
    ]
    # suite = unittest.TestLoader(.loadTestsFromModule(__import__("test"))
    suite = unittest.TestSuite()
    suite.addTests(tests)
    res = unittest.TextTestRunner().run(suite)
