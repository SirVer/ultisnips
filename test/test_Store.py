# encoding: utf-8
import os

from test.vim_test_case import VimTestCase as _VimTest
from test.constant import EX, JF, ESC
from test.util import running_on_windows


class Store_TmpSimple(_VimTest):
  snippets = (
      ('test', '`!p snip.store.tmp["Test"]="tt"``!p snip.rv=snip.store.tmp["Test", ""]`'),
      ('test2', '`!p snip.rv=snip.store.tmp["Test", ""]`'),
  )
  keys = 'test' + EX + ' test2' + EX
  wanted = ' '
    
class Store_TmpPlaceHolderAssign(_VimTest):
  """Store should remember last value in current python code block (and increment assign should work too)"""
  sleeptime = 0.05 # this one needs to have some time betweend inputs
  snippets = (
      ('test','$1`!p\n'
          'if snip.store.tmp["t1", None] != t[1]:\n'
          '  snip.store.tmp["Test",""] +=t[1]\n'
          '  snip.store.tmp["t1"] = t[1]\n'
          'snip.rv=snip.store.tmp["Test"]`'
          '`!p snip.rv=snip.store.tmp["Test","_"]`'
      ),
      ('test2', '`!p snip.rv=snip.store.tmp["Test", ""]`'),
  )
  keys = 'test' + EX + 'ab' + JF + ' test2' + EX
  # first block do the increment :  (t[1]='') '' -> (t[1]='a') 'a' -> (t[1]='a') 'aab'
  # second block has a different store and the key is not present, so print default
  # second snippet neither
  wanted = 'abaab_ ' 
  
class Store_TmpCalledTwice(_VimTest):
  """Store should be reset the second time the snip is called"""
  snippets = ('test', '$1`!p snip.rv=snip.store.tmp["Test",""]; snip.store.tmp["Test"]=t[1]`')
  keys = 'test' + EX + 'ab' + JF + '\ntest' + EX
  wanted = 'abab\n'
  
  


class Store_SnippetSimple(_VimTest):
  snippets = (
      ('test', '`!p snip.store.snippet["Test"]="tt"``!p snip.rv=snip.store.snippet["Test", ""]`'),
      ('test2', '`!p snip.rv=snip.store.snippet["Test", ""]`'),
  )
  keys = 'test' + EX + ' test2' + EX
  wanted = 'tt '
    
class Store_SnippetPlaceHolderAssign(_VimTest):
  """Store should remember last value in current python code block (and increment assign should work too)"""
  sleeptime = 0.05 # this one needs to have some time betweend inputs
  snippets = (
      ('test','$1`!p\n'
          'if snip.store.snippet["t1", None] != t[1]:\n'
          '  snip.store.snippet["Test",""] +=t[1]\n'
          '  snip.store.snippet["t1"] = t[1]\n'
          'snip.rv=snip.store.snippet["Test"]`'
          '`!p snip.rv=snip.store.snippet["Test","_"]`'
      ),
      ('test2', '`!p snip.rv=snip.store.snippet["Test", ""]`'),
  )
  keys = 'test' + EX + 'ab' + JF + ' test2' + EX
  # first block do the increment :  (t[1]='') '' -> (t[1]='a') 'a' -> (t[1]='a') 'aab'
  # second block has access to the value, and print the final value at the end
  # second snippet has a different store and the key is not present, so print default
  wanted = 'abaabaab '
  
  
class Store_SnippetCalledTwice(_VimTest):
  """Store should be reset the second time  the snip is called"""
  snippets = ('test', '$1`!p if t[1]:snip.store.snippet["Test"]=t[1]``!p snip.rv=snip.store.snippet["Test",""]`')
  keys = 'test' + EX + 'tt' + JF + '\ntest' + EX
  wanted = 'tttt\n'
  
  
  
  
class Store_BufferSimple(_VimTest):
  snippets = (
      ('test', '`!p snip.store.buffer["Test"]="tt"``!p snip.rv=snip.store.buffer["Test", ""]`'),
      ('test2', '`!p snip.rv=snip.store.buffer["Test", ""]`'),
  )
  keys = 'test' + EX + ' test2' + EX
  wanted = 'tt tt'
    
class Store_BufferPlaceHolderAssign(_VimTest):
  """Store should remember last value in current python code block (and increment assign should work too)"""
  sleeptime = 0.05 # this one needs to have some time betweend inputs
  snippets = (
      ('test','$1`!p\n'
          'if snip.store.buffer["t1", None] != t[1]:\n'
          '  snip.store.buffer["Test",""] +=t[1]\n'
          '  snip.store.buffer["t1"] = t[1]\n'
          'snip.rv=snip.store.buffer["Test"]`'
          '`!p snip.rv=snip.store.buffer["Test","_"]`'
      ),
      ('test2', '`!p snip.rv=snip.store.buffer["Test", ""]`'),
  )
  keys = 'test' + EX + 'ab' + JF + ' test2' + EX
  # first block do the increment :  (t[1]='') '' -> (t[1]='a') 'a' -> (t[1]='a') 'aab'
  # second block has access to the value, and print the final value at the end
  # second snippet has also the the same store and print the final value
  wanted = 'abaabaab aab'
  
class Store_BufferCalledTwice(_VimTest):
  """Store should be reset the second time the snip is called"""
  snippets = ('test', '$1`!p snip.rv=snip.store.buffer["Test",""]; snip.store.buffer["Test"]=t[1]`')
  keys = 'test' + EX + 'ab' + JF + '\ntest' + EX
  wanted = 'abab\n'




class Store_SessionSimple(_VimTest):
  snippets = (
      ('test', '`!p snip.store.session["Test"]="tt"``!p snip.rv=snip.store.session["Test", ""]`'),
      ('test2', '`!p snip.rv=snip.store.session["Test", ""]`'),
  )
  keys = 'test' + EX + ' test2' + EX
  wanted = 'tt tt'
    
class Store_SessionPlaceHolderAssign(_VimTest):
  """Store should remember last value in current python code block (and increment assign should work too)"""
  sleeptime = 0.05 # this one needs to have some time betweend inputs
  snippets = (
      ('test','$1`!p\n'
          'if snip.store.session["t1", None] != t[1]:\n'
          '  snip.store.session["Test",""] +=t[1]\n'
          '  snip.store.session["t1"] = t[1]\n'
          'snip.rv=snip.store.session["Test"]`'
          '`!p snip.rv=snip.store.session["Test","_"]`'
      ),
      ('test2', '`!p snip.rv=snip.store.session["Test", ""]`'),
  )
  keys = 'test' + EX + 'ab' + JF + ' test2' + EX
  # same as buffer
  wanted = 'abaabaab aab'
  
class Store_SessionCalledTwice(_VimTest):
  """Store should be reset the second time the snip is called"""
  snippets = ('test', '$1`!p snip.rv=snip.store.session["Test",""]; snip.store.session["Test"]=t[1]`')
  keys = 'test' + EX + 'ab' + JF + '\ntest' + EX
  wanted = 'abab\n'
  




class Store_FileSimple(_VimTest):
  snippets = (
      ('test', '`!p snip.store.file["Test"]="tt"``!p snip.rv=snip.store.file["Test", ""]`'),
      ('test2', '`!p snip.rv=snip.store.file["Test", ""]`'),
  )
  keys = 'test' + EX + ' test2' + EX
  wanted = 'tt tt'
    
class Store_FilePlaceHolderAssign(_VimTest):
  """Store should remember last value in current python code block (and increment assign should work too)"""
  sleeptime = 0.05 # this one needs to have some time betweend inputs
  snippets = (
      ('test','$1`!p\n'
          'if snip.store.file["t1", None] != t[1]:\n'
          '  snip.store.file["Test",""] +=t[1]\n'
          '  snip.store.file["t1"] = t[1]\n'
          'snip.rv=snip.store.file["Test"]`'
          '`!p snip.rv=snip.store.file["Test","_"]`'
      ),
      ('test2', '`!p snip.rv=snip.store.file["Test", ""]`'),
  )
  keys = 'test' + EX + 'ab' + JF + ' test2' + EX
  # same as buffer
  wanted = 'abaabaab aab'
  
class Store_FileCalledTwice(_VimTest):
  """Store should be reset the second time the snip is called"""
  snippets = ('test', '$1`!p snip.rv=snip.store.file["Test",""]; snip.store.file["Test"]=t[1]`')
  keys = 'test' + EX + 'ab' + JF + '\ntest' + EX
  wanted = 'abab\n'
  




class Store_CommonSimple(_VimTest):
  snippets = (
      ('test', '`!p snip.store.common["Test"]="tt"``!p snip.rv=snip.store.common["Test", ""]`'),
      ('test2', '`!p snip.rv=snip.store.common["Test", ""]`'),
  )
  keys = 'test' + EX + ' test2' + EX
  wanted = 'tt tt'
    
class Store_CommonPlaceHolderAssign(_VimTest):
  """Store should remember last value in current python code block (and increment assign should work too)"""
  sleeptime = 0.05 # this one needs to have some time betweend inputs
  snippets = (
      ('test','$1`!p\n'
          'if snip.store.common["t1", None] != t[1]:\n'
          '  snip.store.common["Test",""] +=t[1]\n'
          '  snip.store.common["t1"] = t[1]\n'
          'snip.rv=snip.store.common["Test"]`'
          '`!p snip.rv=snip.store.common["Test","_"]`'
      ),
      ('test2', '`!p snip.rv=snip.store.common["Test", ""]`'),
  )
  keys = 'test' + EX + 'ab' + JF + ' test2' + EX
  # same as buffer
  wanted = 'abaabaab aab'
  
class Store_CommonCalledTwice(_VimTest):
  """Store should be reset the second time the snip is called"""
  snippets = ('test', '$1`!p snip.rv=snip.store.common["Test",""]; snip.store.common["Test"]=t[1]`')
  keys = 'test' + EX + 'ab' + JF + '\ntest' + EX
  wanted = 'abab\n'
  



class Store_StoreAreDifferent(_VimTest):
  """Each store should be able to hold its own value for a same key"""
  snippets = ('test', '`!p\n'
      'snip.store.tmp["Test"]="t1"\n'
      'snip.store.snippet["Test"]="t2"\n'
      'snip.store.buffer["Test"]="t3"\n'
      'snip.store.session["Test"]="t4"\n'
      'snip.store.file["Test"]="t5"\n'
      'snip.store.common["Test"]="t6"\n'
      'snip.rv = '
        'snip.store.tmp.Test + snip.store.snippet.Test +'
        'snip.store.buffer.Test + snip.store.session.Test +'
        'snip.store.file.Test + snip.store.common.Test'
      '`'
  )
  keys = 'test' + EX
  wanted = 't1t2t3t4t5t6'
