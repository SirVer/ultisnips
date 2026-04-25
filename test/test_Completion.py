from test.constant import COMPL_ACCEPT, COMPL_KW, EX, JB, JF
from test.vim_test_case import VimTestCase as _VimTest


class Completion_SimpleExample_ECR(_VimTest):
    snippets = ("test", "$1 ${1:blah}")
    keys = (
        "superkallifragilistik\ntest"
        + EX
        + "sup"
        + COMPL_KW
        + COMPL_ACCEPT
        + " some more"
    )
    wanted = (
        "superkallifragilistik\nsuperkallifragilistik some more "
        "superkallifragilistik some more"
    )


# We need >2 different words with identical starts to create the
# popup-menu:
COMPLETION_OPTIONS = "completion1\ncompletion2\n"


class Completion_ForwardsJumpWithoutCOMPL_ACCEPT(_VimTest):
    # completions should not be truncated when JF is activated without having
    # pressed COMPL_ACCEPT (Bug #598903)
    snippets = ("test", "$1 $2")
    keys = COMPLETION_OPTIONS + "test" + EX + "com" + COMPL_KW + JF + "foo"
    wanted = COMPLETION_OPTIONS + "completion1 foo"


class Completion_BackwardsJumpWithoutCOMPL_ACCEPT(_VimTest):
    # completions should not be truncated when JB is activated without having
    # pressed COMPL_ACCEPT (Bug #598903)
    snippets = ("test", "$1 $2")
    keys = COMPLETION_OPTIONS + "test" + EX + "foo" + JF + "com" + COMPL_KW + JB + "foo"
    wanted = COMPLETION_OPTIONS + "foo completion1"


# https://github.com/SirVer/ultisnips/issues/1380 (and #1327) — when the
# completion popup is visible at the moment an iA autosnippet fires, nested
# expansions and the subsequent forward-jumps get confused and end up in
# select mode over a previous placeholder. 'k' then replaces that content.
#
# Reporter's exact repro: nest `frac` three times with the popup open, then
# three forward-jumps + 'k'. Buggy output is ``\frac{\frac{k}{}}{}`` —
# 'k' replaced the already-filled inner ``\frac{}{}`` instead of landing at
# the outermost second-slot or past it.


class Popup_NestedAutosnippet_DoesNotJumpBackward(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet frac "Fraction" iA
        \frac{${1:${VISUAL}}}{$2}$0
        endsnippet
        """
    }
    # Pre-fill the buffer with words starting with 'frac' so COMPL_KW has
    # something to offer. These must live in text_before, NOT in `keys`,
    # because typing "fraction" / "fracture" / "fractal" would trigger the
    # iA snippet on each 'frac' substring.
    text_before = "fraction fracture fractal --- some text before --- \n\n"
    # First `frac` is typed without the popup — InsertCharPre does not fire
    # for the very first characters typed inside a fresh popup session, so
    # iA would never see the trigger if the popup were open from the start.
    # Real users hit the bug after already being inside a snippet when the
    # popup pops up (as coc.nvim or deoplete would cause on typing).
    keys = "frac" + COMPL_KW + "frac" + COMPL_KW + "frac" + JF + JF + JF + "k"
    # Expected (non-buggy) behaviour: three forward-jumps from the innermost
    # first-slot should walk through innermost $2, middle $2, outer $2 (or
    # past $0), and 'k' lands at the outermost slot — never replacing the
    # filled inner ``\frac{}{}``.
    # `wanted` is the content between text_before / text_after — the
    # framework wraps it. Three JFs from innermost T1 walk:
    #   inner T1 → inner T2 → (T0 & pop) → middle T2
    # where 'k' is typed. Hitting $0 exits that nesting level but doesn't
    # auto-advance through the parent, so 3 JFs = middle T2, not outer T2.
    wanted = r"\frac{\frac{\frac{}{}}{k}}{}"

    def _extra_vim_config(self, vim_config):
        # Without `noinsert`, Vim auto-inserts the first popup match as you
        # type (that's why 'some' was leaking into the buffer earlier).
        # `noselect` keeps the popup visible without committing a choice,
        # which is exactly the scenario the bug needs.
        vim_config.append("set completeopt=menu,menuone,noinsert,noselect")


# Same as above, but without auto trigger.
class Popup_NestedNonAutosnippet_DoesNotJumpBackward(_VimTest):
    snippets = ("frac", r"\frac{${1:${VISUAL}}}{$2}$0", "", "i")
    text_before = "fraction fracture fractal --- some text before --- \n\n"
    keys = (
        COMPL_KW
        + "frac"
        + EX
        + COMPL_KW
        + "frac"
        + EX
        + COMPL_KW
        + "frac"
        + EX
        + JF
        + JF
        + JF
        + "k"
    )
    # `wanted` is the content between text_before / text_after — the
    # framework wraps it. Three JFs from innermost T1 walk:
    #   inner T1 → inner T2 → (T0 & pop) → middle T2
    # where 'k' is typed. Hitting $0 exits that nesting level but doesn't
    # auto-advance through the parent, so 3 JFs = middle T2, not outer T2.
    wanted = r"\frac{\frac{\frac{}{}}{k}}{}"

    def _extra_vim_config(self, vim_config):
        vim_config.append("set completeopt=menu,menuone,noinsert,noselect")


# Control: identical expansion/jump sequence but without opening the
# completion popup. Should pass — establishes that the nesting + jump logic
# itself is fine, and it's the popup interaction that breaks it.
class NoPopup_NestedNonAutosnippet_DoesNotJumpBackward(_VimTest):
    snippets = ("frac", r"\frac{${1:${VISUAL}}}{$2}$0", "", "i")
    text_before = "fraction fracture fractal --- some text before --- \n\n"
    keys = "frac" + EX + "frac" + EX + "frac" + EX + JF + JF + JF + "k"
    wanted = r"\frac{\frac{\frac{}{}}{k}}{}"


# https://github.com/SirVer/ultisnips/issues/1400 — reporter's exact case:
# `\test{$1}{$2}$0` iA, nested 5 deep with a completion engine open. They saw
# select-mode landing on a previous placeholder, and the next keystroke
# replaced its content. Same root cause as #1380/#1327; this is the same fix
# (PR #1620), exercised at the depth they reported.
class Popup_DeeplyNestedAutosnippet_Issue1400(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet test "test" iA
        \test{${1:${VISUAL}}}{$2}$0
        endsnippet
        """
    }
    text_before = "tester testing tested --- some text before --- \n\n"
    keys = (
        "test"
        + COMPL_KW
        + "test"
        + COMPL_KW
        + "test"
        + COMPL_KW
        + "test"
        + COMPL_KW
        + "test"
        + JF
        + JF
        + JF
        + JF
        + JF
        + "k"
    )
    # 5 JFs from innermost T1 walk (per the same logic documented above):
    #   L5 T1 → L5 T2 → (T0 & pop) → L4 T2 → (T0 & pop) → L3 T2
    # 'k' lands at L3's $2.
    wanted = r"\test{\test{\test{\test{\test{}{}}{}}{k}}{}}{}"

    def _extra_vim_config(self, vim_config):
        vim_config.append("set completeopt=menu,menuone,noinsert,noselect")
