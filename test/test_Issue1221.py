"""Regression tests for autotrigger expansions with completion popup visible.

Originally filed:
- #1221: `\\begin` bA trigger with body starting `\\\\begin\\{$1}` —
         reporter saw the `{` after `\\begin` eaten when YCM was loaded.
- #1450: `fra` wA trigger with body `\\frac{$1}{$2} $0` —
         reporter saw the trigger left untouched and the first chars of
         the body missing when a completion plugin was active.

Both reporters identified YCM as the catalyst. The popup-interaction class
of bugs (queued buffer edits not applied before expand) was addressed by
PR #1620 for the nested-snippet case. These tests pin down the top-level
case for the exact snippet definitions in the issues, including the
popup-visible variant via Vim's built-in keyword completion.
"""

from test.constant import COMPL_KW
from test.vim_test_case import VimTestCase as _VimTest


# Baselines: no popup.
class Issue1221_NoPopup_BeginExpands(_VimTest):
    files = {
        "us/all.snippets": "\n".join(
            [
                'snippet \\begin "begin{arg}" bA',
                r"\\begin\{${1}}",
                "${0:${VISUAL}}",
                r"\\end\{$1}",
                "endsnippet",
            ]
        )
    }
    keys = "\\begin"
    wanted = "\\begin{}\n\n\\end{}"


class Issue1450_NoPopup_FracExpands(_VimTest):
    files = {
        "us/all.snippets": "\n".join(
            [
                'snippet fra "Frac" wA',
                r"\frac{$1}{$2} $0",
                "endsnippet",
            ]
        )
    }
    keys = "fra"
    wanted = r"\frac{}{} "


# Popup-visible variants. Vim's built-in keyword completion stays visible
# (completeopt=noinsert,noselect) while extra letters are typed; the iA
# autotrigger fires with the popup still up.
class Issue1450_KeywordPopup_FracExpands(_VimTest):
    files = {
        "us/all.snippets": "\n".join(
            [
                'snippet fra "Frac" wA',
                r"\frac{$1}{$2} $0",
                "endsnippet",
            ]
        )
    }
    text_before = "fraction fracture fractal --- some text before --- \n\n"
    keys = COMPL_KW + "fra"
    wanted = r"\frac{}{} "

    def _extra_vim_config(self, vim_config):
        vim_config.append("set completeopt=menu,menuone,noinsert,noselect")


class Issue1221_KeywordPopup_BeginExpands(_VimTest):
    files = {
        "us/all.snippets": "\n".join(
            [
                'snippet \\begin "begin{arg}" bA',
                r"\\begin\{${1}}",
                "${0:${VISUAL}}",
                r"\\end\{$1}",
                "endsnippet",
            ]
        )
    }
    text_before = "\\beginning \\beginner \\begins --- some text before --- \n\n"
    keys = COMPL_KW + "\\begin"
    wanted = "\\begin{}\n\n\\end{}"

    def _extra_vim_config(self, vim_config):
        vim_config.append("set completeopt=menu,menuone,noinsert,noselect")
