"""Tests for how snippet directories are discovered along 'runtimepath'.

Vim allows wildcards in 'runtimepath' entries (see :help 'runtimepath'), so
`find_all_snippet_directories` expands them. Doing that by globbing the whole
entry from the filesystem root made Python 3.12 list every directory on the
way down, once per runtimepath entry. On slow filesystems that froze Vim for
seconds on the first expansion, and an unlistable ancestor directory made the
snippet directory disappear entirely (GH #1694).
"""

from test.constant import ESC, EX
from test.vim_test_case import VimTestCase as _VimTest


class SnippetDirectories_WildcardRuntimepath_ExpandsEntry(_VimTest):
    files = {
        "bundle/alpha/us/foo.snippets": r"""
        snippet hi "Greeting"
        hello
        endsnippet
        """,
    }
    keys = ESC + ":set ft=foo\n" + "ihi" + EX
    wanted = "hello"

    def _extra_vim_config(self, vim_config):
        vim_config.append(f"set runtimepath+={self._temp_dir}/bundle/*")


class SnippetDirectories_WildcardRuntimepath_ExpandsEntryForSnipMate(_VimTest):
    # snipMate discovery used to glob below the unexpanded entry, so a
    # `snippets/` directory behind a wildcard was never found.
    files = {
        "bundle/alpha/snippets/foo.snippets": """
snippet hi
\thello""",
    }
    keys = ESC + ":set ft=foo\n" + "ihi" + EX
    wanted = "hello"

    def _extra_vim_config(self, vim_config):
        vim_config.append(f"set runtimepath+={self._temp_dir}/bundle/*")


class SnippetDirectories_LiteralRuntimepath_DoesNotListDirectories(_VimTest):
    # The harness puts three literal entries on 'runtimepath'. Resolving them
    # must not list a single directory: an existence check per entry is all
    # it takes. The helper reports every directory `os.scandir` gets called
    # for, so a regression names the offending directories in the diff.
    files = {
        "us/foo.snippets": r"""
        snippet hi "Greeting"
        hello
        endsnippet
        """,
    }
    keys = ""
    text_before = ""
    text_after = ""

    @property
    def wanted(self):
        return f"found: {self._temp_dir / 'us'}\nlisted: <none>"

    def _before_test(self):
        helper = self._temp_dir / "_list_snippet_dirs.py"
        helper.write_text(
            "import os, traceback, vim\n"
            "from UltiSnips.snippet.source.file.ulti_snips import ("
            "find_all_snippet_directories)\n"
            f"temp_dir = {str(self._temp_dir)!r}\n"
            "listed = []\n"
            "real_scandir = os.scandir\n"
            "def recording(path='.', *args, **kwargs):\n"
            "    listed.append(str(path))\n"
            "    return real_scandir(path, *args, **kwargs)\n"
            "os.scandir = recording\n"
            "try:\n"
            "    found = find_all_snippet_directories()\n"
            "    lines = ['found: ' + d for d in found if d.startswith(temp_dir)]\n"
            "    lines.append('listed: ' + (', '.join(sorted(set(listed)))"
            " or '<none>'))\n"
            "except Exception:\n"
            "    lines = traceback.format_exc().splitlines()\n"
            "finally:\n"
            "    os.scandir = real_scandir\n"
            "vim.current.buffer[:] = lines\n"
        )
        self.vim.send_to_vim(f":py3file {helper}\n")
