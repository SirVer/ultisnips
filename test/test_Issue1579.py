"""Documentation test for #1579 example 1.

The reporter wants `$N` in the outer body to mirror `$N` in a
pre_expand-created inner anon snippet. UltiSnips never has — each
call to `expand_anon` is its own snippet with its own tabstop
namespace; the outer's $1 and the inner's $1 are unrelated objects.
Jumping fills them in nesting order, not by index.

Pinning the observable behaviour so it can't drift silently.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class Issue1579_TabstopNamespacesAreIndependent(_VimTest):
    files = {
        "us/all.snippets": r"""
        pre_expand "snip.buffer[snip.line] = ''; snip.expand_anon('[$1][$2]')"
        snippet try "try"
        ($1)($2)
        endsnippet
        """
    }
    keys = "try" + EX + "A" + JF + "B" + JF + "C" + JF + "D"
    wanted = "[(A)(B)C][D]"
