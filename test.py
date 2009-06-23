#!/usr/bin/env python
# encoding: utf-8
#

import vim
import unittest

from PySnipEmu import PySnipSnippets


class _VimTest(unittest.TestCase):
    def setUp(self):
        vim.command(":new")
        try:
            self.cmd()
            self.output = '\n'.join(vim.current.buffer[:])
        finally:
            vim.command(":q!")
   
    def insert(self,string):
        """A helper function to type some text"""
        vim.command('normal i%s' % string)

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
    def setUp(self):
        PySnipSnippets.add_snippet("hallo","Hallo Welt!")
        
        _VimTest.setUp(self)

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
    def cmd(self):
        PySnipSnippets.add_snippet("hallo","Hallo Welt!\nUnd Wie gehts?")
        self.insert("Wie hallo gehts?")
        vim.command("normal 02f ")
        self.expand()

    def runTest(self):
        self.assertEqual(self.output, "Wie Hallo Welt!\nUnd Wie gehts? gehts?")

############
# TabStops #
############
class ExitTabStop_ExceptCorrectTrue(_VimTest):
    def cmd(self):
        PySnipSnippets.add_snippet("echo","$0 run")
        self.insert("echo ")
        self.expand()
        self.insert("test")

    def runTest(self):
        self.assertEqual(self.output,"test run ")
    
        
if __name__ == '__main__':
    import sys
    from cStringIO import StringIO

    s = StringIO()
    
    suite = unittest.TestLoader().loadTestsFromModule(__import__("test"))
    res = unittest.TextTestRunner(stream=s).run(suite)
    
    if res.wasSuccessful():
        vim.command("qa!")

    vim.current.buffer[:] = s.getvalue().split('\n')

