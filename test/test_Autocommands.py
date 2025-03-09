# encoding: utf-8
from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Autocommands(_VimTest):
    snippets = ("test", "[ ${1:foo} ]")
    args = ""
    keys = (
        "test"
        + EX
        + "test"
        + EX
        + "bar"
        + JF
        + JF
        + " done "
        + ESC
        + ':execute "normal aM" . g:mapper_call_count . "\\<Esc>"'
        + "\n"
        + ':execute "normal aU" . g:unmapper_call_count . "\\<Esc>"'
        + "\n"
    )
    wanted = "[ [ bar ] ] done M1U1"

    def _extra_vim_config(self, vim_config):
        vim_config.append("let g:mapper_call_count = 0")
        vim_config.append("function! CustomMapper()")
        vim_config.append("  let g:mapper_call_count += 1")
        vim_config.append("endfunction")

        vim_config.append("let g:unmapper_call_count = 0")
        vim_config.append("function! CustomUnmapper()")
        vim_config.append("  let g:unmapper_call_count += 1")
        vim_config.append("endfunction")

        vim_config.append("autocmd! User UltiSnipsEnterFirstSnippet")
        vim_config.append("autocmd User UltiSnipsEnterFirstSnippet call CustomMapper()")
        vim_config.append("autocmd! User UltiSnipsExitLastSnippet")
        vim_config.append("autocmd User UltiSnipsExitLastSnippet call CustomUnmapper()")
