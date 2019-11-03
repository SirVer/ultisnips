from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *


class Bug1251994(_VimTest):
    snippets = ("test", "${2:#2} ${1:#1};$0")
    keys = "  test" + EX + "hello" + JF + "world" + JF + "blub"
    wanted = "  world hello;blub"


# Test for https://github.com/SirVer/ultisnips/issues/157 (virtualedit)


class VirtualEdit(_VimTest):
    snippets = ("pd", "padding: ${1:0}px")
    keys = "\t\t\tpd" + EX + "2"
    wanted = "\t\t\tpadding: 2px"

    def _extra_vim_config(self, vim_config):
        vim_config.append("set virtualedit=all")
        vim_config.append("set noexpandtab")


# End: 1251994

# Test for Github Pull Request #134 - Retain unnamed register


class RetainsTheUnnamedRegister(_VimTest):
    snippets = ("test", "${1:hello} ${2:world} ${0}")
    keys = "yank" + ESC + "by4lea test" + EX + "HELLO" + JF + JF + ESC + "p"
    wanted = "yank HELLO world yank"


class RetainsTheUnnamedRegister_ButOnlyOnce(_VimTest):
    snippets = ("test", "${1:hello} ${2:world} ${0}")
    keys = (
        "blahfasel"
        + ESC
        + "v"
        + 4 * ARR_L
        + "xotest"
        + EX
        + ESC
        + ARR_U
        + "v0xo"
        + ESC
        + "p"
    )
    wanted = "\nblah\nhello world "


# End: Github Pull Request # 134

# Test to ensure that shiftwidth follows tabstop when it's set to zero post
# version 7.3.693. Prior to that version a shiftwidth of zero effectively
# removes tabs.


class ShiftWidthZero(_VimTest):
    def _extra_vim_config(self, vim_config):
        vim_config += ["if exists('*shiftwidth')", "  set shiftwidth=0", "endif"]

    snippets = ("test", "\t${1}${0}")
    keys = "test" + EX + "foo"
    wanted = "\tfoo"


# Test for https://github.com/SirVer/ultisnips/issues/171
# Make sure that we don't crash when trying to save and restore the clipboard
# when it contains data that we can't coerce into Unicode.


class NonUnicodeDataInUnnamedRegister(_VimTest):
    snippets = ("test", "hello")
    keys = (
        "test"
        + EX
        + ESC
        + "\n".join(
            [
                ":redir @a",
                ":messages",
                ":redir END",
                (
                    ":if match(@a, 'Error') != -1 | "
                    + "call setline('.', 'error detected') | "
                    + "3put a | "
                    + "endif"
                ),
                "",
            ]
        )
    )
    wanted = "hello"

    def _before_test(self):
        # The string below was the one a user had on their clipboard when
        # encountering the UnicodeDecodeError and could not be coerced into
        # unicode.
        self.vim.send_to_vim(
            ':let @" = "\\x80kdI{\\x80@7 1},'
            + '\\x80kh\\x80kh\\x80kd\\x80kdq\\x80kb\\x1b"\n'
        )


# End: #171
