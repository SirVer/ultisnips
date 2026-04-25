import os

from test.constant import ESC, EX, JF
from test.util import running_on_windows
from test.vim_test_case import VimTestCase as _VimTest


class TabStop_Shell_SimpleExample(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "hi `echo hallo` you!")
    keys = "test" + EX + "and more"
    wanted = "hi hallo you!and more"


class TabStop_Shell_WithUmlauts(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "hi `echo höüäh` you!")
    keys = "test" + EX + "and more"
    wanted = "hi höüäh you!and more"


class TabStop_Shell_TextInNextLine(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "hi `echo hallo`\nWeiter")
    keys = "test" + EX + "and more"
    wanted = "hi hallo\nWeiterand more"


class TabStop_Shell_InDefValue_Leave(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "Hallo ${1:now `echo fromecho`} end")
    keys = "test" + EX + JF + "and more"
    wanted = "Hallo now fromecho endand more"


class TabStop_Shell_InDefValue_Overwrite(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "Hallo ${1:now `echo fromecho`} end")
    keys = "test" + EX + "overwrite" + JF + "and more"
    wanted = "Hallo overwrite endand more"


class TabStop_Shell_TestEscapedChars_Overwrite(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", r"""`echo \`echo "\\$hi"\``""")
    keys = "test" + EX
    wanted = "$hi"


class TabStop_Shell_TestEscapedCharsAndShellVars_Overwrite(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", r"""`hi="blah"; echo \`echo "$hi"\``""")
    keys = "test" + EX
    wanted = "blah"


class TabStop_Shell_ShebangPython(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = (
        "test",
        """Hallo ${{1:now `#!/usr/bin/env {}
print("Hallo Welt")
`}} end""".format(os.environ.get("PYTHON", "python3")),
    )
    keys = "test" + EX + JF + "and more"
    wanted = "Hallo now Hallo Welt endand more"


class TabStop_VimScriptInterpolation_SimpleExample(_VimTest):
    snippets = ("test", """hi `!v indent(".")` End""")
    keys = "    test" + EX
    wanted = "    hi 4 End"


class PythonCodeOld_SimpleExample(_VimTest):
    snippets = ("test", """hi `!p res = "Hallo"` End""")
    keys = "test" + EX
    wanted = "hi Hallo End"


class PythonCodeOld_ReferencePlaceholderAfter(_VimTest):
    snippets = ("test", """${1:hi} `!p res = t[1]+".blah"` End""")
    keys = "test" + EX + "ho"
    wanted = "ho ho.blah End"


class PythonCodeOld_ReferencePlaceholderBefore(_VimTest):
    snippets = ("test", """`!p res = len(t[1])*"#"`\n${1:some text}""")
    keys = "test" + EX + "Hallo Welt"
    wanted = "##########\nHallo Welt"


class PythonCodeOld_TransformedBeforeMultiLine(_VimTest):
    snippets = (
        "test",
        """${1/.+/egal/m} ${1:`!p
res = "Hallo"`} End""",
    )
    keys = "test" + EX
    wanted = "egal Hallo End"


class PythonCodeOld_IndentedMultiline(_VimTest):
    snippets = (
        "test",
        """start `!p a = 1
b = 2
if b > a:
    res = "b isbigger a"
else:
    res = "a isbigger b"` end""",
    )
    keys = "    test" + EX
    wanted = "    start b isbigger a end"


class PythonCode_UseNewOverOld(_VimTest):
    snippets = (
        "test",
        """hi `!p res = "Old"
snip.rv = "New"` End""",
    )
    keys = "test" + EX
    wanted = "hi New End"


class PythonCode_SimpleExample(_VimTest):
    snippets = ("test", """hi `!p snip.rv = "Hallo"` End""")
    keys = "test" + EX
    wanted = "hi Hallo End"


class PythonCode_SimpleExample_ReturnValueIsEmptyString(_VimTest):
    snippets = ("test", """hi`!p snip.rv = ""`End""")
    keys = "test" + EX
    wanted = "hiEnd"


class PythonCode_ReferencePlaceholder(_VimTest):
    snippets = ("test", """${1:hi} `!p snip.rv = t[1]+".blah"` End""")
    keys = "test" + EX + "ho"
    wanted = "ho ho.blah End"


class PythonCode_ReferencePlaceholderBefore(_VimTest):
    snippets = ("test", """`!p snip.rv = len(t[1])*"#"`\n${1:some text}""")
    keys = "test" + EX + "Hallo Welt"
    wanted = "##########\nHallo Welt"


class PythonCode_TransformedBeforeMultiLine(_VimTest):
    snippets = (
        "test",
        """${1/.+/egal/m} ${1:`!p
snip.rv = "Hallo"`} End""",
    )
    keys = "test" + EX
    wanted = "egal Hallo End"


class PythonCode_MultilineIndented(_VimTest):
    snippets = (
        "test",
        """start `!p a = 1
b = 2
if b > a:
    snip.rv = "b isbigger a"
else:
    snip.rv = "a isbigger b"` end""",
    )
    keys = "    test" + EX
    wanted = "    start b isbigger a end"


class PythonCode_SimpleAppend(_VimTest):
    snippets = (
        "test",
        """hi `!p snip.rv = "Hallo1"
snip += "Hallo2"` End""",
    )
    keys = "test" + EX
    wanted = "hi Hallo1\nHallo2 End"


class PythonCode_MultiAppend(_VimTest):
    snippets = (
        "test",
        """hi `!p snip.rv = "Hallo1"
snip += "Hallo2"
snip += "Hallo3"` End""",
    )
    keys = "test" + EX
    wanted = "hi Hallo1\nHallo2\nHallo3 End"


class PythonCode_MultiAppendSimpleIndent(_VimTest):
    snippets = (
        "test",
        """hi
`!p snip.rv="Hallo1"
snip += "Hallo2"
snip += "Hallo3"`
End""",
    )
    keys = (
        """
    test"""
        + EX
    )
    wanted = """
    hi
    Hallo1
    Hallo2
    Hallo3
    End"""


class PythonCode_SimpleMkline(_VimTest):
    snippets = (
        "test",
        r"""hi
`!p snip.rv="Hallo1\n"
snip.rv += snip.mkline("Hallo2") + "\n"
snip.rv += snip.mkline("Hallo3")`
End""",
    )
    keys = (
        """
    test"""
        + EX
    )
    wanted = """
    hi
    Hallo1
    Hallo2
    Hallo3
    End"""


class PythonCode_MultiAppendShift(_VimTest):
    snippets = (
        "test",
        r"""hi
`!p snip.rv="i1"
snip += "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 3
snip += "i3"`
End""",
    )
    keys = (
        """
	test"""
        + EX
    )
    wanted = """
	hi
	i1
	i1
		i2
i0
			i3
	End"""


class PythonCode_MultiAppendShiftMethods(_VimTest):
    snippets = (
        "test",
        r"""hi
`!p snip.rv="i1\n"
snip.rv += snip.mkline("i1\n")
snip.shift(1)
snip.rv += snip.mkline("i2\n")
snip.unshift(2)
snip.rv += snip.mkline("i0\n")
snip.shift(3)
snip.rv += snip.mkline("i3")`
End""",
    )
    keys = (
        """
	test"""
        + EX
    )
    wanted = """
	hi
	i1
	i1
		i2
i0
			i3
	End"""


class PythonCode_ResetIndent(_VimTest):
    snippets = (
        "test",
        r"""hi
`!p snip.rv="i1"
snip >> 1
snip += "i2"
snip.reset_indent()
snip += "i1"
snip << 1
snip += "i0"
snip.reset_indent()
snip += "i1"`
End""",
    )
    keys = (
        """
	test"""
        + EX
    )
    wanted = """
	hi
	i1
		i2
	i1
i0
	i1
	End"""


class PythonCode_IndentEtSw(_VimTest):
    def _extra_vim_config(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set expandtab")

    snippets = (
        "test",
        r"""hi
`!p snip.rv = "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 1
snip += "i1"
`
End""",
    )
    keys = """   test""" + EX
    wanted = """   hi
   i1
      i2
i0
   i1
   End"""


class PythonCode_IndentEtSwOffset(_VimTest):
    def _extra_vim_config(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set expandtab")

    snippets = (
        "test",
        r"""hi
`!p snip.rv = "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 1
snip += "i1"
`
End""",
    )
    keys = """    test""" + EX
    wanted = """    hi
    i1
       i2
 i0
    i1
    End"""


class PythonCode_IndentNoetSwTs(_VimTest):
    def _extra_vim_config(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set ts=4")

    snippets = (
        "test",
        r"""hi
`!p snip.rv = "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 1
snip += "i1"
`
End""",
    )
    keys = """   test""" + EX
    wanted = """   hi
   i1
\t  i2
i0
   i1
   End"""


# Test using 'opt'


class PythonCode_OptExists(_VimTest):
    def _extra_vim_config(self, vim_config):
        vim_config.append('let g:UStest="yes"')

    snippets = ("test", r"""hi `!p snip.rv = snip.opt("g:UStest") or "no"` End""")
    keys = """test""" + EX
    wanted = """hi yes End"""


class PythonCode_OptNoExists(_VimTest):
    snippets = ("test", r"""hi `!p snip.rv = snip.opt("g:UStest") or "no"` End""")
    keys = """test""" + EX
    wanted = """hi no End"""


class PythonCode_IndentProblem(_VimTest):
    # A test case which is likely related to bug 719649
    snippets = (
        "test",
        r"""hi `!p
snip.rv = "World"
` End""",
    )
    keys = " " * 8 + "test" + EX  # < 8 works.
    wanted = """        hi World End"""


class PythonCode_TrickyReferences(_VimTest):
    snippets = ("test", r"""${2:${1/.+/egal/}} ${1:$3} ${3:`!p snip.rv = "hi"`}""")
    keys = "ups test" + EX
    wanted = "ups egal hi hi"


# locals


class PythonCode_Locals(_VimTest):
    snippets = (
        "test",
        r"""hi `!p a = "test"
snip.rv = "nothing"` `!p snip.rv = a
` End""",
    )
    keys = """test""" + EX
    wanted = """hi nothing test End"""


class PythonCode_LongerTextThanSource_Chars(_VimTest):
    snippets = ("test", r"""hi`!p snip.rv = "a" * 100`end""")
    keys = """test""" + EX + "ups"
    wanted = "hi" + 100 * "a" + "endups"


class PythonCode_LongerTextThanSource_MultiLine(_VimTest):
    snippets = ("test", r"""hi`!p snip.rv = "a" * 100 + '\n'*100 + "a"*100`end""")
    keys = """test""" + EX + "ups"
    wanted = "hi" + 100 * "a" + 100 * "\n" + 100 * "a" + "endups"


class PythonCode_AccessKilledTabstop_OverwriteSecond(_VimTest):
    snippets = (
        "test",
        r"`!p snip.rv = t[2].upper()`${1:h${2:welt}o}`!p snip.rv = t[2].upper()`",
    )
    keys = "test" + EX + JF + "okay"
    wanted = "OKAYhokayoOKAY"


class PythonCode_AccessKilledTabstop_OverwriteFirst(_VimTest):
    snippets = (
        "test",
        r"`!p snip.rv = t[2].upper()`${1:h${2:welt}o}`!p snip.rv = t[2].upper()`",
    )
    keys = "test" + EX + "aaa"
    wanted = "aaa"


class PythonCode_CanOverwriteTabstop(_VimTest):
    snippets = (
        "test",
        """$1`!p if len(t[1]) > 3 and len(t[2]) == 0:
            t[2] = t[1][2:];
            t[1] = t[1][:2] + '-\\n\\t';
            vim.command('call feedkeys("\\\\<End>", "n")');
            `$2""",
    )
    keys = "test" + EX + "blah" + ", bah"
    wanted = "bl-\n\tah, bah"


class PythonVisual_NoVisualSelection_Ignore(_VimTest):
    snippets = ("test", "h`!p snip.rv = snip.v.mode + snip.v.text`b")
    keys = "test" + EX + "abc"
    wanted = "hbabc"


class PythonVisual_SelectOneWord(_VimTest):
    snippets = ("test", "h`!p snip.rv = snip.v.mode + snip.v.text`b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX
    wanted = "hvblablubb"


class PythonVisual_LineSelect_Simple(_VimTest):
    snippets = ("test", "h`!p snip.rv = snip.v.mode + snip.v.text`b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX
    wanted = "hVhello\nnice\nworld\nb"


class PythonVisual_HasAccessToSelectedPlaceholders(_VimTest):
    snippets = (
        "test",
        """${1:first} ${2:second} (`!p
snip.rv = "placeholder: " + snip.p.current_text`)""",
    )
    keys = "test" + EX + ESC + "otest" + EX + JF + ESC
    wanted = """first second (placeholder: first)
first second (placeholder: second)"""


class PythonVisual_HasAccessToZeroPlaceholders(_VimTest):
    snippets = (
        "test",
        """${1:first} ${2:second} (`!p
snip.rv = "placeholder: " + snip.p.current_text`)""",
    )
    keys = "test" + EX + ESC + "otest" + EX + JF + JF + JF + JF
    wanted = """first second (placeholder: first second (placeholder: ))
first second (placeholder: )"""


# Issue #1405: same pattern as PythonVisual_HasAccessToSelectedPlaceholders, but
# with the !p block placed before the tabstops. The reporter claimed this
# variant exposed a cursor / selection sync bug.
class PythonVisual_ReversedHasAccessToSelectedPlaceholders(_VimTest):
    snippets = (
        "test",
        """(`!p
snip.rv = "placeholder: " + snip.p.current_text`) ${1:first} ${2:second}""",
    )
    keys = "test" + EX + ESC + "otest" + EX + JF + ESC
    wanted = """(placeholder: first) first second
(placeholder: second) first second"""


# Issue #1405: zero-length tabstop preceded by a `!p` that evaluates to "" on
# first expansion exposes the cursor-sync bug the reporter pinpointed in
# vim_helper.select() (`i` vs `a` choice for zero-length tabstops).
class Issue1405_EmptyPythonBeforeZeroLengthTabstop(_VimTest):
    snippets = ("test", "`!p snip.rv = ''`abc$1def")
    keys = "test" + EX + "X"
    wanted = "abcXdef"


class Issue1405_EmptyPythonAtStartZeroLengthTabstopMid(_VimTest):
    snippets = ("test", "`!p snip.rv = ''`$1abc")
    keys = "test" + EX + "X"
    wanted = "Xabc"


class Issue1405_EmptyPythonZeroLengthTabstopEnd(_VimTest):
    snippets = ("test", "abc$1`!p snip.rv = ''`")
    keys = "test" + EX + "X"
    wanted = "abcX"


# First tabstop is zero-length and sits right after an empty !p block —
# the closest reconstruction of the issue's "ZeroLength_Trivial" repro.
class Issue1405_ZeroLengthTabstopAfterEmptyPython(_VimTest):
    snippets = ("test", "(`!p snip.rv = ''`)$1 ${2:second}")
    keys = "test" + EX + "X" + JF + "Y"
    wanted = "()X Y"


class Python_SnipRvCanBeNonText(_VimTest):
    # Test for https://github.com/SirVer/ultisnips/issues/1132
    snippets = ("test", "`!p snip.rv = 5`")
    keys = "test" + EX
    wanted = "5"


# https://github.com/SirVer/ultisnips/issues/1403 — two `!p` blocks at the
# same start position (back-to-back, both initially empty) had no stable
# tiebreaker in `TextObject.__lt__`, so `sorted(set_of_objects)` fell back
# to set iteration order. The producer ran after the consumer, the
# convergence loop never re-ran the consumer (its text already matched its
# stale rv=''), and the inter-block dependency silently dropped.
class PythonCode_SameStartCol_OrderedBySource_Issue1403(_VimTest):
    snippets = (
        "test",
        "`!p import sys; sys.modules['ut_1403_marker'] = 'tt'; snip.rv = ''`"
        "`!p import sys; snip.rv = sys.modules.get('ut_1403_marker', '')`",
    )
    keys = "test" + EX
    wanted = "tt"


# https://github.com/SirVer/ultisnips/issues/1402 — a `!p` block that
# converges in two evaluations (because rv depends on side-effect state
# set by the first call). Before the fix in PythonCode._update, the
# convergence loop exited after the first call (ct == rv == ""), the
# snippet end was still at column 0, _jump placed the cursor there, and
# the *second* update_textobjects (driven by _jump) wrote "tt" to the
# buffer but could no longer move the cursor — the user's first keystroke
# landed at the wrong end ("Xtt" instead of "ttX").
class PythonCode_TwoStepConverge_RvExplicitlyEmpty_Issue1402(_VimTest):
    snippets = (
        "test1402a",
        """`!p
import sys
if 'ut_1402_a' not in sys.modules:
    sys.modules['ut_1402_a'] = 'tt'
    snip.rv = ''
else:
    snip.rv = 'tt'
`""",
    )
    keys = "test1402a" + EX + "X"
    wanted = "ttX"


class PythonCode_TwoStepConverge_RvNotMutated_Issue1402(_VimTest):
    snippets = (
        "test1402b",
        """`!p
import sys
if 'ut_1402_b' not in sys.modules:
    sys.modules['ut_1402_b'] = 'tt'
    # snip.rv is intentionally not mutated on first execution
else:
    snip.rv = 'tt'
`""",
    )
    keys = "test1402b" + EX + "X"
    wanted = "ttX"
