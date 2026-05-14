"""Regression test for #1360.

`:UltiSnipsEdit!` must list SnipMate snippet files in addition to
UltiSnips files when `g:UltiSnipsEnableSnipMate` is on. The picker list
is built from ``SnippetManager.all_snippet_files_for(ft)``; here we
exercise that helper directly through ``py3`` so we don't have to drive
the interactive ``inputlist()`` prompt.
"""

from test.vim_test_case import VimTestCase as _VimTest

_QUERY = """
import os
import vim
from UltiSnips import UltiSnips_Manager

files = sorted(UltiSnips_Manager.all_snippet_files_for("blubi"))
# Keep only the last two path components so the assertion does not
# depend on the (random) temp directory name.
short = [os.sep.join(f.split(os.sep)[-2:]) for f in files]
vim.current.buffer[:] = [" ".join(short)]
"""


class Issue1360_EditBangListsSnipMate(_VimTest):
    files = {
        "us/blubi.snippets": "snippet usonly\nfrom ultisnips dir\nendsnippet\n",
        "snippets/blubi.snippets": "snippet smonly\n\tfrom snipmate dir\n",
    }
    keys = ""
    text_before = ""
    text_after = ""
    wanted = "snippets/blubi.snippets us/blubi.snippets"

    def _extra_vim_config(self, vim_config):
        self._create_file("query_1360.py", _QUERY)

    def _before_test(self):
        self.vim.send_to_vim(f":py3file {self.name_temp('query_1360.py')}\n")
