"""Regression tests for `snip.mkline` when the user constructs a multi-line
string in one expression instead of appending line-by-line (GH #1233).

`snip.mkline` infers "is this the first line of the python block's output?"
from `self._rv`. That works for the `snip += line` pattern (which mutates
`snip.rv` between calls), but if the user builds the result in a single
expression - `snip.rv = mkline(...) + "\\n" + mkline(...)` - both calls
see an empty `_rv` and both strip the snippet's initial indent, so every
line after the first under-indents.
"""

from test.constant import EX
from test.vim_test_case import VimTestCase as _VimTest


class Mkline_TwoCallsInOneExpression_BothShifted(_VimTest):
    snippets = (
        "test",
        r"""hi
`!p
snip.shift()
snip.rv = snip.mkline("hello()") + "\n" + snip.mkline("hello()")`
end""",
    )
    keys = "\ttest" + EX
    wanted = "\thi\n\t\thello()\n\t\thello()\n\tend"


class Mkline_GeneratorJoin_AllShifted(_VimTest):
    snippets = (
        "test",
        r"""hi
`!p
snip.shift()
snip.rv = "\n".join(snip.mkline(x) for x in ("a", "b", "c"))`
end""",
    )
    keys = "\ttest" + EX
    wanted = "\thi\n\t\ta\n\t\tb\n\t\tc\n\tend"


# The OP's pattern in GH #1233: `snip.mkline` called twice with `map`,
# joined with newlines. Same root cause as the two-call test above.
class Mkline_MapJoin_AllShifted(_VimTest):
    snippets = (
        "test",
        r"""hi
`!p
snip.shift()
snip.rv = "\n".join(map(snip.mkline, ["a", "b", "c"]))`
end""",
    )
    keys = "\ttest" + EX
    wanted = "\thi\n\t\ta\n\t\tb\n\t\tc\n\tend"
