#!/usr/bin/env python
# encoding: utf-8
#

import vim
import unittest

from PySnipEmu import PySnipSnippets


class _VimTest(unittest.TestCase):
    def setUp(self):
        PySnipSnippets.reset()

        for sv,content in self.snippets:
            PySnipSnippets.add_snippet(sv,content)

        vim.command(":new")
        try:
            self.cmd()
            self.output = '\n'.join(vim.current.buffer[:])
        finally:
            vim.command(":q!")

    def insert(self,string):
        """A helper function to type some text"""
        vim.command('normal i%s' % string)
    def change(self,string):
        """A helper function to type some text"""
        vim.command('normal c%s' % string)

    def expand(self):
        vim.command("call PyVimSnips_ExpandSnippet()")

    def tearDown(self):
        PySnipSnippets.clear_snippets()

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
        self.insert("hallo ")
        self.expand()

    def runTest(self):
        self.assertEqual(self.output,"Hallo Welt! ")

class SimpleExpandTypeAfterExpand_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.insert("hallo ")
        self.expand()
        self.insert("and again")

    def runTest(self):
        self.assertEqual(self.output,"Hallo Welt!and again ")

class SimpleExpandTypeAfterExpand1_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.insert("na du hallo ")
        self.expand()
        self.insert("and again")

    def runTest(self):
        self.assertEqual(self.output,"na du Hallo Welt!and again ")

class DoNotExpandAfterSpace_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.insert("hallo  ")
        self.expand()

    def runTest(self):
        self.assertEqual(self.output,"hallo  ")

class ExpandInTheMiddleOfLine_ExceptCorrectResult(_SimpleExpands):
    def cmd(self):
        self.insert("Wie hallo gehts?")
        vim.command("normal 02f ")
        self.expand()

    def runTest(self):
        self.assertEqual(self.output,"Wie Hallo Welt! gehts?")

class MultilineExpand_ExceptCorrectResult(_VimTest):
    snippets = (
        ("hallo", "Hallo Welt!\nUnd Wie gehts?"),
    )

    def cmd(self):
        self.insert("Wie hallo gehts?")
        vim.command("normal 02f ")
        self.expand()

    def runTest(self):
        self.assertEqual(self.output, "Wie Hallo Welt!\nUnd Wie gehts? gehts?")
class MultilineExpandTestTyping_ExceptCorrectResult(_VimTest):
    snippets = (
        ("hallo", "Hallo Welt!\nUnd Wie gehts?"),
    )

    def cmd(self):
        self.insert("Wie hallo gehts?")
        vim.command("normal 02f ")
        self.expand()
        self.insert("Huiui!")

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
        self.insert("echo ")
        self.expand()
        self.insert("test")

    def runTest(self):
        self.assertEqual(self.output,"test run ")

class TextTabStopNoReplace_ExceptCorrectResult(_VimTest):
    snippets = (
        ("echo", "echo ${1:Hallo}"),
    )

    def cmd(self):
        self.insert("echo ")
        self.expand()

    def runTest(self):
        self.assertEqual(self.output,"echo Hallo ")

class TextTabStopSimpleReplace_ExceptCorrectResult(_VimTest):
    snippets = (
        ("hallo", "hallo ${0:End} ${1:Beginning}"),
    )

    def cmd(self):
        self.insert("hallo ")
        self.expand()
        vim.command(r'call feedkeys("na")')
    
    def runTest(self):
        self.assertEqual(self.output,"hallo End na ")

if __name__ == '__main__':
    import sys
    from cStringIO import StringIO

    s = StringIO()

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
    res = unittest.TextTestRunner(stream=s).run(suite)

    # if res.wasSuccessful():
    #     vim.command("qa!")

    vim.current.buffer[:] = s.getvalue().split('\n')

