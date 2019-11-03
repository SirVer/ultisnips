from test.vim_test_case import VimTestCase as _VimTest
from test.constant import EX, ESC


class SnippetPriorities_MultiWordTriggerOverwriteExisting(_VimTest):
    snippets = (
        ("test me", "${1:Hallo}", "Types Hallo"),
        ("test me", "${1:World}", "Types World"),
        ("test me", "We overwrite", "Overwrite the two", "", 1),
    )
    keys = "test me" + EX
    wanted = "We overwrite"


class SnippetPriorities_DoNotCareAboutNonMatchings(_VimTest):
    snippets = (
        ("test1", "Hallo", "Types Hallo"),
        ("test2", "We overwrite", "Overwrite the two", "", 1),
    )
    keys = "test1" + EX
    wanted = "Hallo"


class SnippetPriorities_OverwriteExisting(_VimTest):
    snippets = (
        ("test", "${1:Hallo}", "Types Hallo"),
        ("test", "${1:World}", "Types World"),
        ("test", "We overwrite", "Overwrite the two", "", 1),
    )
    keys = "test" + EX
    wanted = "We overwrite"


class SnippetPriorities_OverwriteTwice_ECR(_VimTest):
    snippets = (
        ("test", "${1:Hallo}", "Types Hallo"),
        ("test", "${1:World}", "Types World"),
        ("test", "We overwrite", "Overwrite the two", "", 1),
        ("test", "again", "Overwrite again", "", 2),
    )
    keys = "test" + EX
    wanted = "again"


class SnippetPriorities_OverwriteThenChoose_ECR(_VimTest):
    snippets = (
        ("test", "${1:Hallo}", "Types Hallo"),
        ("test", "${1:World}", "Types World"),
        ("test", "We overwrite", "Overwrite the two", "", 1),
        ("test", "No overwrite", "Not overwritten", "", 1),
    )
    keys = "test" + EX + "1\n\n" + "test" + EX + "2\n"
    wanted = "We overwrite\nNo overwrite"


class SnippetPriorities_AddedHasHigherThanFile(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet test "Test Snippet" b
        This is a test snippet
        endsnippet
        """
    }
    snippets = (("test", "We overwrite", "Overwrite the two", "", 1),)
    keys = "test" + EX
    wanted = "We overwrite"


class SnippetPriorities_FileHasHigherThanAdded(_VimTest):
    files = {
        "us/all.snippets": r"""
        snippet test "Test Snippet" b
        This is a test snippet
        endsnippet
        """
    }
    snippets = (("test", "We do not overwrite", "Overwrite the two", "", -1),)
    keys = "test" + EX
    wanted = "This is a test snippet"


class SnippetPriorities_FileHasHigherThanAdded_neg_prio(_VimTest):
    files = {
        "us/all.snippets": r"""
        priority -3
        snippet test "Test Snippet" b
        This is a test snippet
        endsnippet
        """
    }
    snippets = (("test", "We overwrite", "Overwrite the two", "", -5),)
    keys = "test" + EX
    wanted = "This is a test snippet"


class SnippetPriorities_SimpleClear(_VimTest):
    files = {
        "us/all.snippets": r"""
        priority 1
        clearsnippets
        priority -1
        snippet test "Test Snippet"
        Should not expand to this.
        endsnippet
        """
    }
    keys = "test" + EX
    wanted = "test" + EX


class SnippetPriorities_SimpleClear2(_VimTest):
    files = {
        "us/all.snippets": r"""
        clearsnippets
        snippet test "Test snippet"
        Should not expand to this.
        endsnippet
        """
    }
    keys = "test" + EX
    wanted = "test" + EX


class SnippetPriorities_ClearedByParent(_VimTest):
    files = {
        "us/p.snippets": r"""
        clearsnippets
        """,
        "us/c.snippets": r"""
        extends p
        snippet test "Test snippets"
        Should not expand to this.
        endsnippet
        """,
    }
    keys = ESC + ":set ft=c\n" + "itest" + EX
    wanted = "test" + EX


class SnippetPriorities_ClearedByChild(_VimTest):
    files = {
        "us/p.snippets": r"""
        snippet test "Test snippets"
        Should only expand in p.
        endsnippet
        """,
        "us/c.snippets": r"""
        extends p
        clearsnippets
        """,
    }
    keys = (
        ESC
        + ":set ft=p\n"
        + "itest"
        + EX
        + "\n"
        + ESC
        + ":set ft=c\n"
        + "itest"
        + EX
        + ESC
        + ":set ft=p"
    )
    wanted = "Should only expand in p.\ntest" + EX
