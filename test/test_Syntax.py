"""Regression tests for the snippets-filetype syntax file."""

from test.vim_test_case import VimTestCase as _VimTest

_CHECK_HELPER = r"""
import vim

def _groups(line, col):
    return [vim.eval('synIDattr(' + str(sid) + ', "name")')
            for sid in vim.eval('synstack(' + str(line) + ',' + str(col) + ')')]

def _has(name, line, col):
    return name in _groups(line, col)

# Buffer layout for issue #1468 -- column numbers are 1-indexed:
#
# Line 3:  '\t${2:${VISUAL:\/\* code \*\/}}'
#           1 = '\t'
#           2 = '$'  3 = '{'  4 = '2'  5 = ':'
#           6 = '$'  7 = '{'  8..13 = 'VISUAL'
#          14 = ':'  15 = '\'  16 = '/'  17 = '\'  18 = '*'
#          19 = ' '  20..23 = 'code'  24 = ' '
#          25 = '\'  26 = '*'  27 = '\'  28 = '/'
#          29 = '}'  30 = '}'

checks = []

# Plain text inside ${VISUAL:...} must register as snipVisualDefault.
checks.append('plain_in_default=' + ('OK' if _has('snipVisualDefault', 3, 18)
                                     else 'FAIL:' + ','.join(_groups(3, 18))))
checks.append('letter_in_default=' + ('OK' if _has('snipVisualDefault', 3, 20)
                                      else 'FAIL:' + ','.join(_groups(3, 20))))

# The escaped slash itself must be recognised as an escape, not as the
# start of a transformation.
checks.append('escaped_slash=' + ('OK' if _has('snipTransformationEscape', 3, 15)
                                  else 'FAIL:' + ','.join(_groups(3, 15))))

# The trailing escape sequence right before the closing brace must also
# stay inside snipVisualDefault -- otherwise the visual region runs past
# the closing brace and the following snippet stops being recognised.
checks.append('closing_escape=' + ('OK' if _has('snipTransformationEscape', 3, 27)
                                   else 'FAIL:' + ','.join(_groups(3, 27))))

# The next snippet definition (line 6) must still be parsed as a header.
checks.append('next_snippet=' + ('OK' if _has('snipSnippetHeader', 6, 1)
                                 else 'FAIL:' + ','.join(_groups(6, 1))))

vim.current.buffer[:] = [' '.join(checks)]
"""


class Syntax_VisualEscapedSlashDefault_1468(_VimTest):
    """Regression for #1468: escaped slashes inside a ${VISUAL:default}
    must not be treated as the start of a transformation by the snippets
    syntax file. If they are, every following line gets the wrong
    highlight group and even the next snippet header bleeds into the
    previous snippet's transformation."""

    keys = ""
    wanted = (
        "plain_in_default=OK letter_in_default=OK escaped_slash=OK"
        " closing_escape=OK next_snippet=OK"
    )
    text_before = ""
    text_after = ""

    _snippet_lines = [
        'snippet if "if block"',
        "if (${1:default}) {",
        "\t${2:${VISUAL:\\/\\* code \\*\\/}}",
        "}",
        "endsnippet",
        'snippet next "second snippet"',
        "after-text",
        "endsnippet",
    ]

    def _extra_vim_config(self, vim_config):
        self._create_file(
            "issue_1468_setup.py",
            "import vim\n"
            "vim.current.buffer[:] = " + repr(self._snippet_lines) + "\n",
        )
        self._create_file("issue_1468_check.py", _CHECK_HELPER)

    def _before_test(self):
        # `set buftype=nofile` plus filetype=snippets is enough to drive the
        # syntax engine without touching disk. Populate the buffer with the
        # bug sample, force a full syntax sync, then write the verdict back
        # into the buffer for the framework to read.
        self.vim.send_to_vim(
            f":py3file {self.name_temp('issue_1468_setup.py')}\n"
        )
        self.vim.send_to_vim(":setfiletype snippets\n")
        self.vim.send_to_vim(":syntax sync fromstart\n")
        self.vim.send_to_vim(":redraw!\n")
        self.vim.send_to_vim(
            f":py3file {self.name_temp('issue_1468_check.py')}\n"
        )
