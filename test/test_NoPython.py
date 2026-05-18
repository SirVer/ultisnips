"""Regression tests for #1237 (and #1209's symptom):

If the Python 3 interpreter or the UltiSnips package can't be loaded,
the plugin must disable itself instead of spamming a stack trace on
every keystroke.

We can't actually launch Vim without Python (the test framework needs
it), so we simulate the import failure: after the normal plugin load,
poison `sys.modules['UltiSnips']`, clear the `did_plugin_ultisnips`
guard, and re-source `plugin/UltiSnips.vim`. With the fix, the plugin
must `finish` before defining `:UltiSnipsEdit` again.
"""

from test.vim_test_case import VimTestCase as _VimTest


class _ReloadBase(_VimTest):
    keys = ""
    wanted = ""
    text_before = ""
    text_after = ""

    def _reload_plugin_with_broken_import(self):
        """Send commands that simulate the import failure and re-source
        the plugin file."""
        plugin_file = self._repo_root() / "plugin" / "UltiSnips.vim"
        self.vim.send_to_vim(":let g:UltiSnipsNoPythonWarning = 1\n")
        # Poison UltiSnips's `sys.modules` entry so the plugin's
        # `from UltiSnips import UltiSnips_Manager` raises ImportError.
        # We do this *after* the test framework's own import succeeded.
        self.vim.send_to_vim(":py3 import sys\n")
        self.vim.send_to_vim(
            ":py3 for _k in [k for k in list(sys.modules) "
            "if k == 'UltiSnips' or k.startswith('UltiSnips.')]: "
            "del sys.modules[_k]\n"
        )
        self.vim.send_to_vim(":py3 sys.modules['UltiSnips'] = None\n")
        self.vim.send_to_vim(":unlet! did_plugin_ultisnips\n")
        self.vim.send_to_vim(":silent! delcommand UltiSnipsEdit\n")
        self.vim.send_to_vim(":silent! autocmd! UltiSnips_AutoTrigger\n")
        self.vim.send_to_vim(f":source {plugin_file}\n")

    def _repo_root(self):
        from pathlib import Path

        return Path(__file__).resolve().parent.parent


class NoPython_PluginBailsBeforeRegisteringCommand(_ReloadBase):
    """After the simulated import failure, `:UltiSnipsEdit` must NOT
    exist - the plugin has bailed before reaching the `command!` line."""

    wanted = "exists=0"

    def _before_test(self):
        self._reload_plugin_with_broken_import()
        self.vim.send_to_vim(
            ":py3 vim.current.buffer[:] = "
            '[\'exists=\' + vim.eval(\'exists(":UltiSnipsEdit") ? "1" : "0"\')]\n'
        )


class NoPython_NoSpamOnInsertModeKeystrokes(_ReloadBase):
    """With the plugin disabled, the autocmds are unregistered, so
    typing in insert mode produces no UltiSnips errors — the buffer just
    receives the typed characters."""

    keys = "hello world"
    wanted = "hello world"

    def _before_test(self):
        self._reload_plugin_with_broken_import()


class NoPython_DiagnosticsCapturedForBugReport(_ReloadBase):
    """Without the silencer, the plugin captures a traceback, the failing
    interpreter's `sys.executable`, and the issues/new URL into
    `g:UltiSnipsPythonDiagnostics` so users can paste it into a bug
    report (#1685)."""

    wanted = "has_traceback=1 has_executable=1 has_url=1"

    def _before_test(self):
        plugin_file = self._repo_root() / "plugin" / "UltiSnips.vim"
        self.vim.send_to_vim(":unlet! g:UltiSnipsNoPythonWarning\n")
        self.vim.send_to_vim(":unlet! g:UltiSnipsPythonDiagnostics\n")
        self.vim.send_to_vim(":py3 import sys\n")
        self.vim.send_to_vim(
            ":py3 for _k in [k for k in list(sys.modules) "
            "if k == 'UltiSnips' or k.startswith('UltiSnips.')]: "
            "del sys.modules[_k]\n"
        )
        self.vim.send_to_vim(":py3 sys.modules['UltiSnips'] = None\n")
        self.vim.send_to_vim(":unlet! did_plugin_ultisnips\n")
        self.vim.send_to_vim(":silent! delcommand UltiSnipsEdit\n")
        self.vim.send_to_vim(":silent! autocmd! UltiSnips_AutoTrigger\n")
        self.vim.send_to_vim(f":source {plugin_file}\n")
        # `botright new` in the plugin opens a diagnostic split and
        # focuses it; close that and return to the test buffer.
        self.vim.send_to_vim(":silent! close\n")
        self.vim.send_to_vim(
            ":py3 _diag = '\\n'.join(vim.eval('g:UltiSnipsPythonDiagnostics'))\n"
        )
        self.vim.send_to_vim(
            ":py3 vim.current.buffer[:] = ["
            "'has_traceback=' + ('1' if 'Traceback' in _diag else '0') + "
            "' has_executable=' + ('1' if 'sys.executable' in _diag else '0') + "
            "' has_url=' + ("
            "'1' if 'github.com/SirVer/ultisnips/issues/new' in _diag else '0'"
            ")]\n"
        )
