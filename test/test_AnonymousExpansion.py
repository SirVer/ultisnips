from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Anonymous Expansion  {{{#


class _AnonBase(_VimTest):
    args = ''

    def _extra_vim_config(self, vim_config):
        vim_config.append('inoremap <silent> %s <C-R>=UltiSnips#Anon(%s)<cr>'
                          % (EA, self.args))


class Anon_NoTrigger_Simple(_AnonBase):
    args = '"simple expand"'
    keys = 'abc' + EA
    wanted = 'abcsimple expand'


class Anon_NoTrigger_AfterSpace(_AnonBase):
    args = '"simple expand"'
    keys = 'abc ' + EA
    wanted = 'abc simple expand'


class Anon_NoTrigger_BeginningOfLine(_AnonBase):
    args = r"':latex:\`$1\`$0'"
    keys = EA + 'Hello' + JF + 'World'
    wanted = ':latex:`Hello`World'


class Anon_NoTrigger_FirstCharOfLine(_AnonBase):
    args = r"':latex:\`$1\`$0'"
    keys = ' ' + EA + 'Hello' + JF + 'World'
    wanted = ' :latex:`Hello`World'


class Anon_NoTrigger_Multi(_AnonBase):
    args = '"simple $1 expand $1 $0"'
    keys = 'abc' + EA + '123' + JF + '456'
    wanted = 'abcsimple 123 expand 123 456'


class Anon_Trigger_Multi(_AnonBase):
    args = '"simple $1 expand $1 $0", "abc"'
    keys = '123 abc' + EA + '123' + JF + '456'
    wanted = '123 simple 123 expand 123 456'


class Anon_Trigger_Simple(_AnonBase):
    args = '"simple expand", "abc"'
    keys = 'abc' + EA
    wanted = 'simple expand'


class Anon_Trigger_Twice(_AnonBase):
    args = '"simple expand", "abc"'
    keys = 'abc' + EA + '\nabc' + EX
    wanted = 'simple expand\nabc' + EX


class Anon_Trigger_Opts(_AnonBase):
    args = '"simple expand", ".*abc", "desc", "r"'
    keys = 'blah blah abc' + EA
    wanted = 'simple expand'
# End: Anonymous Expansion  #}}}
