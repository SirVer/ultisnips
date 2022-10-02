#!/usr/bin/env python3
# encoding: utf-8
#
# See CONTRIBUTING.md for an explanation of this file.
#
# NOTE: The test suite is not working under Windows right now as I have no
# access to a windows system for fixing it. Volunteers welcome. Here are some
# comments from the last time I got the test suite running under windows.
#
# Under windows, COM's SendKeys is used to send keystrokes to the gvim window.
# Note that Gvim must use english keyboard input (choose in windows registry)
# for this to work properly as SendKeys is a piece of chunk. (i.e. it sends
# <F13> when you send a | symbol while using german key mappings)

# pylint: skip-file

import os
import platform
import subprocess
import unittest
from test.vim_interface import (
    create_directory,
    tempfile,
    VimInterfaceTmux,
    VimInterfaceTmuxNeovim,
)


def plugin_cache_dir():
    """The directory that we check out our bundles to."""
    return os.path.join(tempfile.gettempdir(), "UltiSnips_test_vim_plugins")


def clone_plugin(plugin):
    """Clone the given plugin into our plugin directory."""
    dirname = os.path.join(plugin_cache_dir(), os.path.basename(plugin))
    print("Cloning %s -> %s" % (plugin, dirname))
    if os.path.exists(dirname):
        print("Skip cloning of %s. Already there." % plugin)
        return
    create_directory(dirname)
    subprocess.call(
        [
            "git",
            "clone",
            "--recursive",
            "--depth",
            "1",
            "https://github.com/%s" % plugin,
            dirname,
        ]
    )

    if plugin == "Valloric/YouCompleteMe":
        # CLUTCH: this plugin needs something extra.
        subprocess.call(os.path.join(dirname, "./install.sh"), cwd=dirname)


def setup_other_plugins(all_plugins):
    """Creates /tmp/UltiSnips_test_vim_plugins and clones all plugins into
    this."""
    clone_plugin("tpope/vim-pathogen")
    for plugin in all_plugins:
        clone_plugin(plugin)


if __name__ == "__main__":
    import optparse
    import sys

    def parse_args():
        p = optparse.OptionParser("%prog [OPTIONS] <test case names to run>")

        p.set_defaults(
            session="vim", interrupt=False, verbose=False, retries=4, plugins=False
        )

        p.add_option(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="print name of tests as they are executed",
        )
        p.add_option(
            "--clone-plugins",
            action="store_true",
            help="Only clones dependant plugins and exits the test runner.",
        )
        p.add_option(
            "--plugins",
            action="store_true",
            help="Run integration tests with other Vim plugins.",
        )
        p.add_option(
            "-s",
            "--session",
            dest="session",
            metavar="SESSION",
            help="session parameters for the terminal multiplexer SESSION [%default]",
        )
        p.add_option(
            "-i",
            "--interrupt",
            dest="interrupt",
            action="store_true",
            help="Stop after defining the snippet. This allows the user "
            "to interactively test the snippet in vim. You must give "
            "exactly one test case on the cmdline. The test will always fail.",
        )
        p.add_option(
            "-r",
            "--retries",
            dest="retries",
            type=int,
            help="How often should each test be retried before it is "
            "considered failed. Works around flakyness in the terminal "
            "multiplexer and race conditions in writing to the file system.",
        )
        p.add_option(
            "-f",
            "--failfast",
            dest="failfast",
            action="store_true",
            help="Stop the test run on the first error or failure.",
        )
        p.add_option(
            "--vim",
            dest="vim",
            type=str,
            default="vim",
            help="executable to run when launching vim.",
        )
        p.add_option(
            "--interface",
            dest="interface",
            type=str,
            default="tmux",
            help="Interface to use. Use 'tmux' with vanilla Vim and 'tmux_nvim' "
            "with Neovim.",
        )
        p.add_option(
            "--python-host-prog",
            dest="python_host_prog",
            type=str,
            default="",
            help="Neovim needs a variable to tell it which python interpretor to use for "
            "py blocks. This needs to be set to point to the correct python interpretor. "
            "It is ignored for vanilla Vim.",
        )
        p.add_option(
            "--expected-python-version",
            dest="expected_python_version",
            type=str,
            default="",
            help="If set, each test will check sys.version inside of vim to "
            "verify we are testing against the expected Python version.",
        )
        p.add_option(
            "--remote-pdb",
            dest="pdb_enable",
            action="store_true",
            help="If set, The remote pdb server will be run",
        )
        p.add_option(
            "--remote-pdb-host",
            dest="pdb_host",
            type=str,
            default="localhost",
            help="Remote pdb server host",
        )
        p.add_option(
            "--remote-pdb-port",
            dest="pdb_port",
            type=int,
            default=8080,
            help="Remote pdb server port",
        )
        p.add_option(
            "--remote-pdb-non-blocking",
            dest="pdb_block",
            action="store_false",
            help="If set, the server will not freeze vim on error",
        )

        o, args = p.parse_args()
        return o, args

    def flatten_test_suite(suite):
        flatten = unittest.TestSuite()
        for test in suite:
            if isinstance(test, unittest.TestSuite):
                flatten.addTests(flatten_test_suite(test))
            else:
                flatten.addTest(test)
        return flatten

    def main():
        options, selected_tests = parse_args()

        all_test_suites = unittest.defaultTestLoader.discover(start_dir="test")

        has_nvim = subprocess.check_output(
            [options.vim, "-e", "-s", "-c", "verbose echo has('nvim')", "+q"],
            stderr=subprocess.STDOUT,
        )
        if has_nvim == b"0":
            vim_flavor = "vim"
        elif has_nvim == b"1":
            vim_flavor = "neovim"
        else:
            assert 0, "Unexpected output, has_nvim=%r" % has_nvim

        if options.interface == "tmux":
            assert vim_flavor == "vim", (
                "Interface is tmux, but vim_flavor is %s" % vim_flavor
            )
            vim = VimInterfaceTmux(options.vim, options.session)
        else:
            assert vim_flavor == "neovim", (
                "Interface is TmuxNeovim, but vim_flavor is %s" % vim_flavor
            )
            vim = VimInterfaceTmuxNeovim(options.vim, options.session)

        if not options.clone_plugins and platform.system() == "Windows":
            raise RuntimeError(
                "TODO: TestSuite is broken under windows. Volunteers wanted!."
            )
            # vim = VimInterfaceWindows()
            # vim.focus()

        all_other_plugins = set()

        tests = set()
        suite = unittest.TestSuite()

        for test in flatten_test_suite(all_test_suites):
            test.interrupt = options.interrupt
            test.retries = options.retries
            test.test_plugins = options.plugins
            test.python_host_prog = options.python_host_prog
            test.expected_python_version = options.expected_python_version
            test.vim = vim
            test.vim_flavor = vim_flavor
            test.pdb_enable = options.pdb_enable
            test.pdb_host = options.pdb_host
            test.pdb_port = options.pdb_port
            test.pdb_block = options.pdb_block
            all_other_plugins.update(test.plugins)

            if len(selected_tests):
                id = test.id().split(".")[1]
                if not any([id.startswith(t) for t in selected_tests]):
                    continue
            tests.add(test)
        suite.addTests(tests)

        if options.plugins or options.clone_plugins:
            setup_other_plugins(all_other_plugins)
            if options.clone_plugins:
                return

        v = 2 if options.verbose else 1
        successfull = (
            unittest.TextTestRunner(verbosity=v, failfast=options.failfast)
            .run(suite)
            .wasSuccessful()
        )
        return 0 if successfull else 1

    sys.exit(main())
