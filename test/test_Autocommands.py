# encoding: utf-8
from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Autocommands  {{{#

class Autocommands(_VimTest):
    snippets = ('test', '[ ${1:foo} ]')
    args = ''
    keys = 'test' + EX + JF + ESC + \
            ':execute "normal iM" . g:mapper_call_count . "\<Esc>"' + "\n" + \
            ':execute "normal aU" . g:unmapper_call_count . "\<Esc>"' + "\n"
    wanted = '[ foo M1U1]'

    def _extra_options_pre_init(self, vim_config):
        vim_config.append('let g:mapper_call_count = 0')
        vim_config.append('function! CustomMapper()')
        vim_config.append('  let g:mapper_call_count += 1')
        vim_config.append('endfunction')

        vim_config.append('let g:unmapper_call_count = 0')
        vim_config.append('function! CustomUnmapper()')
        vim_config.append('  let g:unmapper_call_count += 1')
        vim_config.append('endfunction')

        vim_config.append('autocmd! User UltiSnipsMapInnerKeys')
        vim_config.append('autocmd User UltiSnipsMapInnerKeys call CustomMapper()')
        vim_config.append('autocmd! User UltiSnipsUnmapInnerKeys')
        vim_config.append('autocmd User UltiSnipsUnmapInnerKeys call CustomUnmapper()')

# end: Autocommands  #}}}
