#!/usr/bin/env python3
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

import platform
import subprocess
import unittest
from pathlib import Path

from test.vim_interface import (
    VimInterfaceTmux,
    create_directory,
    tempfile,
)


def plugin_cache_dir():
    """The directory that we check out our bundles to."""
    return Path(tempfile.gettempdir()) / "UltiSnips_test_vim_plugins"


def clone_plugin(plugin):
    """Clone the given plugin into our plugin directory."""
    dirname = plugin_cache_dir() / Path(plugin).name
    print(f"Cloning {plugin} -> {dirname}")
    if dirname.exists():
        print(f"Skip cloning of {plugin}. Already there.")
        return
    create_directory(dirname)
    subprocess.run(
        [
            "git",
            "clone",
            "--recursive",
            "--depth",
            "1",
            f"https://github.com/{plugin}",
            str(dirname),
        ]
    )

    if plugin == "Valloric/YouCompleteMe":
        # CLUTCH: this plugin needs something extra.
        subprocess.run(str(dirname / "./install.sh"), cwd=str(dirname))


def setup_other_plugins(all_plugins):
    """Creates /tmp/UltiSnips_test_vim_plugins and clones all plugins into
    this."""
    clone_plugin("tpope/vim-pathogen")
    for plugin in all_plugins:
        clone_plugin(plugin)


if __name__ == "__main__":
    import argparse
    import sys

    def parse_args():
        p = argparse.ArgumentParser(
            description="Run UltiSnips test suite.",
            usage="%(prog)s [OPTIONS] [test case names to run]",
        )

        p.add_argument(
            "args",
            nargs="*",
            metavar="test",
            help="test case names to run",
        )
        p.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            action="store_true",
            default=False,
            help="print name of tests as they are executed",
        )
        p.add_argument(
            "--clone-plugins",
            action="store_true",
            help="Only clones dependant plugins and exits the test runner.",
        )
        p.add_argument(
            "--plugins",
            action="store_true",
            default=False,
            help="Run integration tests with other Vim plugins.",
        )
        p.add_argument(
            "-s",
            "--session",
            dest="session",
            metavar="SESSION",
            default="vim",
            help="session parameters for the terminal multiplexer SESSION [%(default)s]",
        )
        p.add_argument(
            "-i",
            "--interrupt",
            dest="interrupt",
            action="store_true",
            default=False,
            help="Stop after defining the snippet. This allows the user "
            "to interactively test the snippet in vim. You must give "
            "exactly one test case on the cmdline. The test will always fail.",
        )
        p.add_argument(
            "-r",
            "--retries",
            dest="retries",
            type=int,
            default=4,
            help="How often should each test be retried before it is "
            "considered failed. Works around flakyness in the terminal "
            "multiplexer and race conditions in writing to the file system.",
        )
        p.add_argument(
            "-f",
            "--failfast",
            dest="failfast",
            action="store_true",
            help="Stop the test run on the first error or failure.",
        )
        p.add_argument(
            "--vim",
            dest="vim",
            type=str,
            default="vim",
            help="executable to run when launching vim.",
        )
        p.add_argument(
            "--python-host-prog",
            dest="python_host_prog",
            type=str,
            default="",
            help="Sets g:python3_host_prog in neovim to select which python "
            "interpreter to use for py3 blocks. Ignored for vanilla Vim.",
        )
        p.add_argument(
            "--expected-python-version",
            dest="expected_python_version",
            type=str,
            default="",
            help="If set, each test will check sys.version inside of vim to "
            "verify we are testing against the expected Python version.",
        )
        p.add_argument(
            "--remote-pdb",
            dest="pdb_enable",
            action="store_true",
            help="If set, The remote pdb server will be run",
        )
        p.add_argument(
            "--remote-pdb-host",
            dest="pdb_host",
            type=str,
            default="localhost",
            help="Remote pdb server host",
        )
        p.add_argument(
            "--remote-pdb-port",
            dest="pdb_port",
            type=int,
            default=8080,
            help="Remote pdb server port",
        )
        p.add_argument(
            "--remote-pdb-non-blocking",
            dest="pdb_block",
            action="store_false",
            help="If set, the server will not freeze vim on error",
        )

        o = p.parse_args()
        return o, o.args

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

        all_other_plugins = set()
        tests = set()
        suite = unittest.TestSuite()

        # Collect tests and their plugin dependencies. We do this before vim
        # detection so that --clone-plugins works without a vim binary.
        for test in flatten_test_suite(all_test_suites):
            all_other_plugins.update(test.plugins)

            if len(selected_tests):
                id = test.id().split(".")[1]
                if not any(id.startswith(t) for t in selected_tests):
                    continue
            tests.add(test)

        if options.plugins or options.clone_plugins:
            setup_other_plugins(all_other_plugins)
            if options.clone_plugins:
                return

        if platform.system() == "Windows":
            raise RuntimeError(
                "TODO: TestSuite is broken under windows. Volunteers wanted!."
            )

        has_nvim = subprocess.check_output(
            [options.vim, "-e", "-s", "-c", "verbose echo has('nvim')", "+q"],
            stderr=subprocess.STDOUT,
        )
        if has_nvim == b"0":
            vim_flavor = "vim"
        elif has_nvim == b"1":
            vim_flavor = "neovim"
        else:
            assert 0, f"Unexpected output, has_nvim={has_nvim!r}"

        vim = VimInterfaceTmux(options.vim, options.session)

        for test in tests:
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
        suite.addTests(tests)

        v = 2 if options.verbose else 1
        successfull = (
            unittest.TextTestRunner(verbosity=v, failfast=options.failfast)
            .run(suite)
            .wasSuccessful()
        )
        return 0 if successfull else 1

    sys.exit(main())
