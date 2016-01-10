from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

# Folding Interaction  {{{#


class FoldingEnabled_SnippetWithFold_ExpectNoFolding(_VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set foldlevel=0')
        vim_config.append('set foldmethod=marker')
    snippets = ('test', r"""Hello {{{
${1:Welt} }}}""")
    keys = 'test' + EX + 'Ball'
    wanted = """Hello {{{
Ball }}}"""


class FoldOverwrite_Simple_ECR(_VimTest):
    snippets = ('fold',
                """# ${1:Description}  `!p snip.rv = vim.eval("&foldmarker").split(",")[0]`

# End: $1  `!p snip.rv = vim.eval("&foldmarker").split(",")[1]`""")
    keys = 'fold' + EX + 'hi'
    wanted = '# hi  {{{\n\n# End: hi  }}}'


class Fold_DeleteMiddleLine_ECR(_VimTest):
    snippets = ('fold',
                """# ${1:Description}  `!p snip.rv = vim.eval("&foldmarker").split(",")[0]`


# End: $1  `!p snip.rv = vim.eval("&foldmarker").split(",")[1]`""")
    keys = 'fold' + EX + 'hi' + ESC + 'jdd'
    wanted = '# hi  {{{\n\n# End: hi  }}}'


class PerlSyntaxFold(_VimTest):

    def _extra_vim_config(self, vim_config):
        vim_config.append('set foldlevel=0')
        vim_config.append('syntax enable')
        vim_config.append('set foldmethod=syntax')
        vim_config.append('let g:perl_fold = 1')
        vim_config.append('so $VIMRUNTIME/syntax/perl.vim')
    snippets = ('test', r"""package ${1:`!v printf('c%02d', 3)`};
${0}
1;""")
    keys = 'test' + EX + JF + 'sub junk {}'
    wanted = 'package c03;\nsub junk {}\n1;'
# End: Folding Interaction  #}}}
