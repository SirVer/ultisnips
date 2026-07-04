from test.constant import ARR_L, ARR_U, CTRL_V, ESC, EX, JB, JF, LS
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


# Test for https://github.com/SirVer/ultisnips/issues/1297 —
# Triggering a snippet directly from visual mode (the xnoremap path)
# must not clobber the unnamed register with the visually-selected text.


class RetainsTheUnnamedRegister_FromVisualMode(_VimTest):
    snippets = ("test", "${1:hello} ${2:world} ${0}")
    keys = (
        "yank "
        + ESC
        + "0y4l"
        + "$a"
        + "VICTIM"
        + ESC
        + "v5h"
        + EX
        + "test"
        + EX
        + "HELLO"
        + JF
        + JF
        + ESC
        + "p"
    )
    wanted = "yank HELLO world yank"


# Test for https://github.com/SirVer/ultisnips/issues/1037 —
# Snippet expansion must not clobber the yank register @0 when the user
# has separated @" and @0 (e.g. by yanking, then deleting/changing).


class PreservesYankRegisterAcrossSnippet(_VimTest):
    snippets = ("test", "[${1:hello}]$0")
    keys = (
        "yank dlt"
        + ESC
        + "0yiw"
        + "$"
        + "B"
        + "diw"
        + "atest"
        + EX
        + "X"
        + JF
        + ESC
        + '"0p'
    )
    wanted = "yank [X]yank"


# Companion to PreservesYankRegisterAcrossSnippet: the same setup, but paste
# from `@"` rather than `@0`. `@"` was last set by `diw` (so points at `@-` /
# `@1`); snippet expansion must restore that state too.


class PreservesUnnamedRegisterAcrossSnippet(_VimTest):
    snippets = ("test", "[${1:hello}]$0")
    keys = (
        "yank dlt"
        + ESC
        + "0yiw"
        + "$"
        + "B"
        + "diw"
        + "atest"
        + EX
        + "X"
        + JF
        + ESC
        + "p"
    )
    wanted = "yank [X]dlt"


# Companion test for `@1`. We line-delete with `dd` (writes to `@1`, not just
# `@-`), then expand a snippet whose placeholder spans two lines — replacing
# it pushes the placeholder text into `@1` and shifts our user state out. The
# fix must restore `@1` to the original `LINE1` line.


class PreservesNumberedRegisterAcrossSnippet(_VimTest):
    snippets = ("test", "[${1:first\nsecond}]$0")
    keys = (
        "LINE1"
        + ESC
        + "dd"
        + "otest"
        + EX
        + "X"
        + JF
        + ESC
        + "o"
        + ESC
        + '"1p'
        + "o"
        + ESC
    )
    wanted = "\n[X]\n\nLINE1"


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


# https://github.com/SirVer/ultisnips/issues/1628 — :bd! while a snippet with
# a !p block is active used to fire CursorMoved against the new buffer before
# the deferred BufEnter teardown ran, leaving the snippet trying to reconcile
# its text-object tree against an unrelated buffer.
class BufferDelete_DropsActiveSnippet_Issue1628(_VimTest):
    text_before = ""
    text_after = ""
    files = {
        "us/all.snippets": r"""
snippet ott
${1:Video} tube`!p snip.rv = '' if t[1] else 's'`.
endsnippet
        """
    }
    keys = "ott" + EX + ESC + ":bd!\n"
    wanted = ""


# Regression tests for #1182 and #193 — `VimBufferProxy._apply_change`
# used to compare line and column independently against the snippet's
# end, dropping any edit whose column was >= the snippet's end column.
# For a multi-line snippet whose end sits at the start of a line
# (`_end.col == 0`, which is the common case) that's *every* edit on
# an interior line. The downstream symptom: a `snip.buffer` mutation in
# a `post_jump` action that runs inside an outer snippet leaves the
# outer's text-object tree pointing at stale (line, col) coordinates,
# producing garbled output and the appearance of tabstops "multiplying".


class Issue1182_NestedDynamicTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def create_row_placeholders(snip):
            placeholders_amount = int(snip.buffer[snip.line].strip())
            snip.buffer[snip.line] = ''
            anon = ' & '.join(['$' + str(i + 1) for i in range(placeholders_amount)])
            snip.expand_anon(anon)
        endglobal

        post_jump "create_row_placeholders(snip)"
        snippet "tr(\d+)" "latex table row" r
        `!p snip.rv = match.group(1)`
        endsnippet

        snippet "\[\[" "display math" r
        \\begin{align*}
            $1
        \\end{align*}
        $0
        endsnippet
        """
    }
    keys = "[[" + EX + "tr2" + EX + "a" + JF + "b"
    wanted = "\\begin{align*}\na & b\n\\end{align*}\n"


class Issue193_AnonAddsLineInsideContainer(_VimTest):
    files = {
        "us/all.snippets": r"""
        global !p
        def insert_extra(snip):
            snip.expand_anon("EXTRA_$1\n")
        endglobal

        post_jump "if snip.tabstop == 1: insert_extra(snip)"
        snippet container "container" b
        A:${1}
        B:${2}
        C:${3}
        endsnippet
        """
    }
    keys = "container" + EX + "x" + JF + JF + "y" + JF + "z"
    wanted = "A:EXTRA_x\n\nB:y\nC:z"


# Regression test for #161 — typing `<Esc>O` immediately after expanding a
# snippet used to race CursorMoved and bleed snippet text into the new line.
# Fixed in passing by the listener-based edit-detection rewrite (#1613).


class Issue161_EscOpenAfterExpand(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet cls "class"
        class ${1:Name}:
            $0
        endsnippet
        """
    }
    keys = "cls" + EX + ESC + "Otop"
    wanted = "top\nclass Name:\n    "


# Regression test for #168 — when ${VISUAL} is empty and immediately followed
# by another tabstop, that tabstop's content used to land outside the
# surrounding quotes; jumping past the first tabstop without editing it left
# the second tabstop at the wrong column.


class Issue168_VisualPlaceholderDoesNotShiftFollowingTabstop(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet se "" b
        ,{
          'AUTHOR': '${1:Williams}',
          'TEXT': '${VISUAL}$2',
        }
        endsnippet
        """
    }
    keys = "se" + EX + JF + "X"
    wanted = ",{\n  'AUTHOR': 'Williams',\n  'TEXT': 'X',\n}"


# Regression test for #1454 — when the user left insert mode, did off-snippet
# work (`o` to open a new line below) and re-entered insert there, the snippet
# used to stay active. The `\n` queued by `o` lands at the snippet's `_end`,
# and the fall-through path in `_do_edit` previously dragged `_end` onto the
# new line — so `_check_if_still_inside_snippet` never noticed the cursor was
# now outside. Refusing to extend `_end` on past-end fall-through restores
# the natural "cursor outside ⇒ drop snippet" path.


class Issue1454_JumpBackAfterOffSnippetEditTerminates(_VimTest):
    snippets = ("fra", r"\frac{$1}{$2}")
    keys = "fra" + EX + "num" + JF + "den" + ESC + "ohi" + JB + "X"
    wanted = "\\frac{num}{den}\nhi" + JB + "X"


# Regression test for #1359 — when adjacent zero-width tabstops/mirrors share
# a position, typing into the active tabstop misattributed the cursor to the
# trailing sibling. The mirror update then dragged the cursor with it, so
# only the first character was mirrored and subsequent characters landed
# in the wrong place (or outside any tabstop).


class Issue1359_AdjacentMirrorTabstop_TypingMirrors(_VimTest):
    snippets = ("test", "$1$1$2(some other things)$0")
    keys = "test" + EX + "words"
    wanted = "wordswords(some other things)"


class Issue1359_AdjacentMirrorTabstop_JumpThenType(_VimTest):
    snippets = ("test", "$1$1$2")
    keys = "test" + EX + "hi" + JF + "x"
    wanted = "hihix"


# Regression test for #503 — the `m` option strips trailing whitespace from
# each line of the snippet at launch time, but ${VISUAL} replaces a single-
# line placeholder with multi-line content during update_textobjects, so
# the line-mode indent prepended to each new line was never stripped.
# Empty visual lines came out as a bare indent string instead of an empty
# line.


class Issue503_MOptionStripsEmptyVisualLines(_VimTest):
    snippets = ("test", "${VISUAL}", "", "m")
    keys = "empty line in visual\n\nshould be empty" + ESC + "V2k" + EX + "\ttest" + EX
    wanted = "\tempty line in visual\n\n\tshould be empty"


# Regression test for the ei14 variant of #1311 — `pair` snippet `($1, $2)`,
# type into $1, `<Esc>`, `o` to drop a new line below, then press the expand
# trigger. With `g:UltiSnipsExpandTrigger == g:UltiSnipsJumpForwardTrigger`
# (Tab mapped via `ExpandSnippetOrJump`), no snippet matches at the new-line
# cursor, so the trigger falls through to `_jump`. Same mechanism as #1454:
# `o` queued a `\n` at end-of-snippet, fall-through used to drag the
# snippet's `_end` onto the new line, the cursor-bounds check then saw the
# cursor inside the (extended) snippet and `_jump` happily jumped back in.
# Refusing to extend on past-end fall-through closes both.


class Issue1311_PairTabAfterModeRoundTrip(_VimTest):
    snippets = ("pair", "($1, $2)")
    # Mirror the ei14 repro by mapping Tab to both expand and jump (the
    # default when the two triggers are identical).
    keys = "pair" + EX + "1" + ESC + "o" + EX
    wanted = "(1, )\n" + EX

    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UltiSnipsExpandTrigger="<tab>"')
        vim_config.append('let g:UltiSnipsJumpForwardTrigger="<tab>"')
        vim_config.append('let g:UltiSnipsJumpBackwardTrigger="<s-tab>"')


# Regression tests for #1691 — the migration from glob.glob to Path.glob
# (#1606) silently changed hidden-file semantics: glob.glob never matches
# names starting with a dot, Path.glob does. Vim drops undo files like
# ".foo.snippets.un~" next to edited snippet files (with 'undofile' set and
# 'undodir' containing "."), and the "ft/*" lookup pattern then picked them
# up and crashed with a UnicodeDecodeError on their binary content. Pin the
# restored pre-#1606 behaviour: hidden files are never snippet sources.


class Issue1691_UndoFileInSnippetSubdirectoryIsIgnored(_VimTest):
    files = {
        "us/all/real.snippets": r"""
        snippet works "from the real file"
        expanded fine
        endsnippet
        """
    }
    keys = "works" + EX
    wanted = "expanded fine"

    def _before_test(self):
        # What Vim writes for real.snippets with 'undodir' set to ".":
        # hidden and not valid UTF-8 (0x9f, the byte from the issue).
        undo_file = self.name_temp("us/all/.real.snippets.un~")
        undo_file.write_bytes(b"Vim\x9f\x00\x01 undo file")


class Issue1691_HiddenSnippetFileIsIgnored(_VimTest):
    """Even a parseable hidden file in ft/* must stay invisible, as it
    was before the Path.glob migration."""

    files = {
        "us/all/.hidden.snippets": r"""
        snippet spooky "from a hidden file"
        BOO
        endsnippet
        """
    }
    keys = "spooky" + EX
    wanted = "spooky" + EX
