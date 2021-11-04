"""
These tests are checking what was once a NON-DETERMINISTIC bug.
An error on any run should be interpreted as a fail.
You should run them a huge amont of times before concluding they passed.

If most of the tests of other files passes but some of this one don't,
then it is highly probable it is a problem with zero length text object ordering.
"""

from test.vim_test_case import VimTestCase as _VimTest
from test.constant import *

class ZeroLength_Simple(_VimTest):
    snippets = ("test", "$1$2")
    keys = "test" + EX + "a" + JF + "b" + JF + "c"
    wanted = "abc"


class ZeroLength_ManyTabs(_VimTest):
    snippets = ("test", "$3$1$5$2$4$6")
    keys = "test" + EX + "a" + JF + "b" + JF + "c" + JF + "d" + JF + "e" + JF + "f" + JF + "g"
    wanted = "caebdfg"


class ZeroLength_SimpleWithMirror(_VimTest):
    snippets = ("test", "$1$1")
    keys = "test" + EX + "a" + JF + "b"
    wanted = "aab"


class ZeroLength_SimpleWithMirrorDefaultEmpty1(_VimTest):
    snippets = ("test", "${1:}$1")
    keys = "test" + EX + "a" + JF + "b"
    wanted = "aab"


class ZeroLength_SimpleWithMirrorDefaultEmpty2(_VimTest):
    snippets = ("test", "$1${1:}")
    keys = "test" + EX + "a" + JF + "b"
    wanted = "aab"


class ZeroLength_ManyTabsWithMirrors(_VimTest):
    snippets = ("test", "$3$1$5$1$5$2$2$4$2$6$1")
    keys = "test" + EX + "a" + JF + "b" + JF + "c" + JF + "d" + JF + "e" + JF + "f" + JF + "g"
    wanted = "caeaebbdbfag"


class ZeroLength_ManyTabsWithMirrorsDefaultEmpty(_VimTest):
    snippets = ("test", "$3$1$5${1:}$5$2$2${4:}$2${6:}$1")
    keys = "test" + EX + "a" + JF + "b" + JF + "c" + JF + "d" + JF + "e" + JF + "f" + JF + "g"
    wanted = "caeaebbdbfag"


class ZeroLength_ManyTabsWithMirrorsDefaultNonEmpty(_VimTest):
    snippets = ("test", "$3$1$5${1:}$5$2$2${4:tdsgq}$2${6:ezgezg}$1")
    keys = "test" + EX + "a" + JF + "b" + JF + "c" + JF + "d" + JF + "e" + JF + "f" + JF + "g"
    wanted = "caeaebbdbfag"


class ZeroLength_ManyTabsWithMirrorsAndPythonMirrors(_VimTest):
    snippets = ("test", "$3$1`!p snip.rv=t[5]`$1$5$2`!p snip.rv=t[2]`$4$2$6$1")
    keys = "test" + EX + "a" + JF + "b" + JF + "c" + JF + "d" + JF + "e" + JF + "f" + JF + "g"
    wanted = "caeaebbdbfag"

class ZeroLength_OriginalBug1(_VimTest):
    snippets = ("test", 
        "`!p\n"
        "import sys\n"
        "if 'dummy' not in sys.modules:\n"
        "	sys.modules['dummy'] = 'tt'\n"
        "	snip.rv=''\n"
        "else:\n"
        "	snip.rv='tt'\n"
        "`"
    )
    keys = "test" + EX + "a"
    wanted = "tta"

class ZeroLength_OriginalBug2(_VimTest):
    snippets = ("test", 
        "`!p\n"
        "import sys\n"
        "if 'dummy' not in sys.modules:\n"
        "	sys.modules['dummy'] = 'tt'\n"
        "	# snip.rv is not mutated\n"
        "else:\n"
        "	snip.rv='tt'\n"
        "`\n"
    )
    keys = "test" + EX + "a"
    wanted = "tta"

class ZeroLength_OriginalBug3(_VimTest):
    snippets = ("test", "`!p import sys;sys.modules['dummy'] = 'tt';snip.rv=''``!p snip.rv=sys.modules.get('dummy', '')`")
    keys = "test" + EX + "a"
    wanted = "tta"
    

class ZeroLength_OriginalBug3bis(_VimTest):
    snippets = ("test", "`!p import sys;sys.modules['dummy'] = 'tt'``!p snip.rv=sys.modules.get('dummy', '')`")
    keys = "test" + EX + "a"
    wanted = "tta"



