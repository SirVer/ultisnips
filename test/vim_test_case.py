# encoding: utf-8

# pylint: skip-file

import os
import subprocess
import tempfile
import textwrap
import time
import unittest

from test.constant import SEQUENCES, EX
from test.vim_interface import create_directory, TempFileManager


def plugin_cache_dir():
    """The directory that we check out our bundles to."""
    return os.path.join(tempfile.gettempdir(), "UltiSnips_test_vim_plugins")


class VimTestCase(unittest.TestCase, TempFileManager):
    snippets = ()
    files = {}
    text_before = " --- some text before --- \n\n"
    text_after = "\n\n --- some text after --- "
    expected_error = ""
    wanted = ""
    keys = ""
    sleeptime = 0.00
    output = ""
    plugins = []
    # Skip this test for the given reason or None for not skipping it.
    skip_if = lambda self: None
    version = None  # Will be set to vim --version output
    maxDiff = None  # Show all diff output, always.
    vim_flavor = None  # will be 'vim' or 'neovim'.
    expected_python_version = (
        None  # If set, we need to check that our Vim is running this python version.
    )

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        TempFileManager.__init__(self, "Case")

    def runTest(self):
        if self.expected_python_version:
            self.assertEqual(self.in_vim_python_version, self.expected_python_version)

        # Only checks the output. All work is done in setUp().
        wanted = self.text_before + self.wanted + self.text_after
        SLEEPTIMES = [0.01, 0.15, 0.3, 0.4, 0.5, 1]
        for i in range(self.retries):
            if self.output and self.expected_error:
                self.assertRegexpMatches(self.output, self.expected_error)
                return
            if self.output != wanted or self.output is None:
                # Redo this, but slower
                self.sleeptime = SLEEPTIMES[min(i, len(SLEEPTIMES) - 1)]
                self.tearDown()
                self.setUp()
        self.assertMultiLineEqual(self.output, wanted)

    def _extra_vim_config(self, vim_config):
        """Adds extra lines to the vim_config list."""

    def _before_test(self):
        """Send these keys before the test runs.

        Used for buffer local variables and other options.

        """

    def _create_file(self, file_path, content):
        """Creates a file in the runtimepath that is created for this test.

        Returns the absolute path to the file.

        """
        return self.write_temp(file_path, textwrap.dedent(content + "\n"))

    def _link_file(self, source, relative_destination):
        """Creates a link from 'source' to the 'relative_destination' in our
        temp dir."""
        absdir = self.name_temp(relative_destination)
        create_directory(absdir)
        os.symlink(source, os.path.join(absdir, os.path.basename(source)))

    def setUp(self):
        if not VimTestCase.version:
            VimTestCase.version, _ = subprocess.Popen(
                [self.vim.vim_executable, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).communicate()
            VimTestCase.version = VimTestCase.version.decode("utf-8")

        if self.plugins and not self.test_plugins:
            return self.skipTest("Not testing integration with other plugins.")
        reason_for_skipping = self.skip_if()
        if reason_for_skipping is not None:
            return self.skipTest(reason_for_skipping)

        vim_config = []
        vim_config.append("set nocompatible")
        vim_config.append(
            "set runtimepath=$VIMRUNTIME,%s,%s"
            % (os.path.dirname(os.path.dirname(__file__)), self._temp_dir)
        )

        if self.plugins:
            self._link_file(
                os.path.join(plugin_cache_dir(), "vim-pathogen", "autoload"), "."
            )
            for plugin in self.plugins:
                self._link_file(
                    os.path.join(plugin_cache_dir(), os.path.basename(plugin)), "bundle"
                )
            vim_config.append("execute pathogen#infect()")

        # Some configurations are unnecessary for vanilla Vim, but Neovim
        # defines some defaults differently.
        vim_config.append("syntax on")
        vim_config.append("filetype plugin indent on")
        vim_config.append("set nosmarttab")
        vim_config.append("set noautoindent")
        vim_config.append('set backspace=""')
        vim_config.append('set clipboard=""')
        vim_config.append("set encoding=utf-8")
        vim_config.append("set fileencoding=utf-8")
        vim_config.append("set buftype=nofile")
        vim_config.append("set shortmess=at")
        vim_config.append('let @" = ""')
        assert EX == "\t"  # Otherwise you need to change the next line
        vim_config.append('let g:UltiSnipsExpandTrigger="<tab>"')
        vim_config.append('let g:UltiSnipsJumpForwardTrigger="?"')
        vim_config.append('let g:UltiSnipsJumpBackwardTrigger="+"')
        vim_config.append('let g:UltiSnipsListSnippets="@"')

        vim_config.append(
            "let g:UltiSnipsDebugServerEnable={}".format(1 if self.pdb_enable else 0)
        )
        vim_config.append('let g:UltiSnipsDebugHost="{}"'.format(self.pdb_host))
        vim_config.append("let g:UltiSnipsDebugPort={}".format(self.pdb_port))
        vim_config.append(
            "let g:UltiSnipsPMDebugBlocking={}".format(1 if self.pdb_block else 0)
        )

        # Work around https://github.com/vim/vim/issues/3117 for testing >
        # py3.7 on Vim 8.1. Actually also reported against UltiSnips
        # https://github.com/SirVer/ultisnips/issues/996
        if "Vi IMproved 8.1" in self.version:
            vim_config.append("silent! python3 1")

        vim_config.append('let g:UltiSnipsSnippetDirectories=["us"]')
        if self.python_host_prog:
            vim_config.append('let g:python3_host_prog="%s"' % self.python_host_prog)

        self._extra_vim_config(vim_config)

        # Finally, add the snippets and some configuration for the test.
        vim_config.append("py3 << EOF")
        vim_config.append("from UltiSnips import UltiSnips_Manager\n")

        if len(self.snippets) and not isinstance(self.snippets[0], tuple):
            self.snippets = (self.snippets,)
        for s in self.snippets:
            sv, content = s[:2]
            description = ""
            options = ""
            priority = 0
            if len(s) > 2:
                description = s[2]
            if len(s) > 3:
                options = s[3]
            if len(s) > 4:
                priority = s[4]
            vim_config.append(
                "UltiSnips_Manager.add_snippet(%r, %r, %r, %r, priority=%i)"
                % (sv, content, description, options, priority)
            )

        # fill buffer with default text and place cursor in between.
        prefilled_text = (self.text_before + self.text_after).splitlines()
        vim_config.append("import vim\n")
        vim_config.append("vim.current.buffer[:] = %r\n" % prefilled_text)
        vim_config.append(
            "vim.current.window.cursor = (max(len(vim.current.buffer)//2, 1), 0)"
        )

        # End of python stuff.
        vim_config.append("EOF")

        for name, content in self.files.items():
            self._create_file(name, content)

        self.in_vim_python_version = self.vim.launch(vim_config)

        self._before_test()

        if not self.interrupt:
            # Go into insert mode and type the keys but leave Vim some time to
            # react.
            text = "i" + self.keys
            while text:
                to_send = None
                for seq in SEQUENCES:
                    if text.startswith(seq):
                        to_send = seq
                        break
                to_send = to_send or text[0]
                self.vim.send_to_vim(to_send)
                time.sleep(self.sleeptime)
                text = text[len(to_send) :]
            self.output = self.vim.get_buffer_data()

    def tearDown(self):
        if self.interrupt:
            print("Working directory: %s" % (self._temp_dir))
            return
        self.vim.leave_with_wait()
        self.clear_temp()


# vim:fileencoding=utf-8:
