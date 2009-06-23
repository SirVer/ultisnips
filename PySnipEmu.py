#!/usr/bin/env python
# encoding: utf-8

import vim
import string

class Snippet(object):
    def __init__(self,trigger,value):
        self._t = trigger
        self._v = value
    
    @property
    def trigger(self):
        return self._t
           
    def _replace_tabstops(self):
        ts = None
        
        lines = self._v.split('\n')
        for idx in range(len(lines)):
            l = lines[idx]
            
            fidx = l.find("$0")
            if fidx != -1:
                ts = idx,fidx
                lines[idx] = l[:idx] + l[idx+2:]
        return ts,lines

    def put(self, before, after):
        lineno,col = vim.current.window.cursor
        
        col -= len(self._t)

        endtab,lines = self._replace_tabstops()
        
        if endtab is not None:
            lineno = lineno + endtab[0]
            col = col + endtab[1]
        else:
            col = col + len(lines[-1])
        
        lines[0] = before + lines[0]
        lines[-1] += after

        vim.current.buffer[lineno-1:lineno-1+len(lines)] = lines
        vim.current.window.cursor = lineno, col
        

class SnippetManager(object):
    def __init__(self):
        self.clear_snippets()
    
    def add_snippet(self,trigger,value):
        self._snippets[trigger] = Snippet(trigger,value)
    
    def clear_snippets(self):
        self._snippets = {}
    
    def try_expand(self):
        line = vim.current.line
        
        dummy,col = vim.current.window.cursor

        if col > 0 and line[col-1] in string.whitespace:
            return

        # Get the word to the left of the current edit position
        before,after = line[:col], line[col:]

        word = before.split()[-1]
        if word in self._snippets:
            self._snippets[word].put(before.rstrip()[:-len(word)], after)


PySnipSnippets = SnippetManager()
