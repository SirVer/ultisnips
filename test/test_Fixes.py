from test.constant import ARR_L, ARR_U, CTRL_V, ESC, EX, JF, LS
from test.vim_test_case import VimTestCase as _VimTest


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


# Test for #1184
# UltiSnips should pass through any mapping that it currently can't execute as
# the trigger key


class PassThroughNonexecutedTrigger(_VimTest):
    snippets = ("text", "Expand me!", "", "")
    keys = (
        "tex"
        + EX
        + "more\n"  # this should be passed through
        + "text"
        + EX  # this should be expanded
    )
    wanted = "tex" + EX + "more\nExpand me!"


# End: #1184


# Tests for the trigger-key fallthrough cluster:
#   #1232 — `<space>` as trigger should still re-emit space on failure
#   #1460 — `<c-j>` as trigger silently overrides `imap <c-j> <nop>`
#   #1482 — `<c-space>` as trigger inserts <t_ü>
#   #1523 — `<a-;>` as trigger inserts <t_u;>
#
# `g:UltiSnipsInsertTriggerOnNoMatch` (default 1) gates the re-emission.
# Users with `<…>`-form triggers whose bytes don't round-trip cleanly as
# text (most special keys other than Tab/Space) set it to 0. <c-j> is the
# easiest of the cluster to drive end-to-end because its byte (LF / 0x0a)
# sends cleanly through tmux; <c-space>/<a-;> hit the identical code path.


class TriggerKey_CtrlJ_DefaultBehaviorReFires(_VimTest):
    """Default `g:UltiSnipsInsertTriggerOnNoMatch=1`: pressing <c-j> with no
    snippet inserts a newline (LF), preserving the historical behaviour."""

    keys = "test\n"
    wanted = "test\n"

    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UltiSnipsExpandTrigger="<c-j>"')


class TriggerKey_CtrlJ_OptOutSuppressesReFire(_VimTest):
    """With `g:UltiSnipsInsertTriggerOnNoMatch=0`, pressing <c-j> with no
    snippet does nothing — closes #1460 and (via the same code path)
    #1482 / #1523 for users who set the option."""

    keys = "test\n"
    wanted = "test"

    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UltiSnipsExpandTrigger="<c-j>"')
        vim_config.append("let g:UltiSnipsInsertTriggerOnNoMatch=0")


class TriggerKey_CtrlJ_StillExpandsSnippet(_VimTest):
    """The opt-out only affects the failure path: when a snippet matches,
    <c-j> still expands it."""

    snippets = ("hello", "Hallo Welt!")
    keys = "hello\n"
    wanted = "Hallo Welt!"

    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UltiSnipsExpandTrigger="<c-j>"')
        vim_config.append("let g:UltiSnipsInsertTriggerOnNoMatch=0")


class TriggerKey_Space_DefaultInsertsSpace(_VimTest):
    """Default behaviour with <space> as trigger: spaces still pass through
    on failed expansion (#1232)."""

    keys = "test "
    wanted = "test "

    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UltiSnipsExpandTrigger="<space>"')


class TriggerKey_Space_OptOutConsumesSpace(_VimTest):
    """With the opt-out, `<space>` is consumed on failure too — documents
    the consistent behaviour for users who pick the more aggressive
    setting."""

    keys = "test "
    wanted = "test"

    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UltiSnipsExpandTrigger="<space>"')
        vim_config.append("let g:UltiSnipsInsertTriggerOnNoMatch=0")


# End: trigger-key fallthrough cluster


# Tests for https://github.com/SirVer/ultisnips/issues/1386 (embedded null byte)


NULL_BYTE = CTRL_V + "000"


class NullByte_ListSnippets(_VimTest):
    snippets = ("word", "never expanded", "", "w")
    keys = "foobar" + NULL_BYTE + LS + "\n"
    wanted = "foobar\x00\n"


class NullByte_ExpandAfter(_VimTest):
    snippets = ("test", "Expand me!", "", "w")
    keys = "foobar " + NULL_BYTE + "test" + EX
    wanted = "foobar \x00Expand me!"


# End: #1386
