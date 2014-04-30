#!/usr/bin/env python
# encoding: utf-8
#
# To execute this test requires two terminals, one for running Vim and one
# for executing the test script. Both terminals should have their current
# working directories set to this directory (the one containing this test.py
# script).
#
# In one terminal, launch a GNU ``screen`` session named ``vim``:
#   $ screen -S vim
#
# Now, from another terminal, launch the testsuite:
#    $ ./test.py
#
# For each test, the test.py script will launch vim with a vimrc, run the test,
# compare the output and exit vim again. The keys are send using screen.
#
# NOTE: The tessuite is not working under Windows right now as I have no access
# to a windows system for fixing it. Volunteers welcome. Here are some comments
# from the last time I got the test suite running under windows.
#
# Under windows, COM's SendKeys is used to send keystrokes to the gvim window.
# Note that Gvim must use english keyboard input (choose in windows registry)
# for this to work properly as SendKeys is a piece of chunk. (i.e. it sends
# <F13> when you send a | symbol while using german key mappings)

# pylint: skip-file

from textwrap import dedent
import os
import platform
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile
import time
import unittest

try:
    import unidecode
    UNIDECODE_IMPORTED = True
except ImportError:
    UNIDECODE_IMPORTED = False

# Some constants for better reading
BS = '\x7f'
ESC = '\x1b'
ARR_L = '\x1bOD'
ARR_R = '\x1bOC'
ARR_U = '\x1bOA'
ARR_D = '\x1bOB'

# multi-key sequences generating a single key press
SEQUENCES = [ARR_L, ARR_R, ARR_U, ARR_D]

# Defined Constants
JF = "?" # Jump forwards
JB = "+" # Jump backwards
LS = "@" # List snippets
EX = "\t" # EXPAND
EA = "#" # Expand anonymous

COMPL_KW = chr(24)+chr(14)
COMPL_ACCEPT = chr(25)

PYTHON3 = sys.version_info >= (3,0)

def running_on_windows():
    if platform.system() == "Windows":
        return "Does not work on Windows."

def python3():
    if PYTHON3:
        return "Test does not work on python3."

def no_unidecode_available():
    if not UNIDECODE_IMPORTED:
        return "unidecode is not available."

def is_process_running(pid):
    """Returns true if a process with pid is running, false otherwise."""
    # from http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def silent_call(cmd):
    """Calls 'cmd' and returns the exit value."""
    return subprocess.call(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

def create_directory(dirname):
    """Creates 'dirname' and its parents if it does not exist."""
    try:
        os.makedirs(dirname)
    except OSError:
        pass

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
    subprocess.call(["git", "clone", "--recursive",
        "--depth", "1", "https://github.com/%s" % plugin, dirname])

    if plugin == "Valloric/YouCompleteMe":
        ## CLUTCH: this plugin needs something extra.
        subprocess.call(os.path.join(dirname, "./install.sh"), cwd=dirname)

def setup_other_plugins(all_plugins):
    """Creates /tmp/UltiSnips_test_vim_plugins and clones all plugins into this."""
    clone_plugin("tpope/vim-pathogen")
    for plugin in all_plugins:
        clone_plugin(plugin)

def read_text_file(filename):
    """Reads the contens of a text file."""
    if PYTHON3:
        return open(filename,"r", encoding="utf-8").read()
    else:
        return open(filename,"r").read()

def random_string(n):
    return ''.join(random.choice(string.ascii_lowercase) for x in range(n))

class VimInterface(object):
    def get_buffer_data(self):
        handle, fn = tempfile.mkstemp(prefix="UltiSnips_Test",suffix=".txt")
        os.close(handle)
        os.unlink(fn)

        self.send(ESC + ":w! %s\n" % fn)

        # Read the output, chop the trailing newline
        tries = 50
        while tries:
            if os.path.exists(fn):
                return read_text_file(fn)[:-1]
            time.sleep(.01)
            tries -= 1

class VimInterfaceScreen(VimInterface):
    def __init__(self, session):
        self.session = session
        self.need_screen_escapes = 0
        self.detect_parsing()

    def send(self, s):
        if self.need_screen_escapes:
            # escape characters that are special to some versions of screen
            repl = lambda m: '\\' + m.group(0)
            s = re.sub( r"[$^#\\']", repl, s )

        if PYTHON3:
            s = s.encode("utf-8")

        while True:
            rv = 0
            if len(s) > 30:
                rv |= silent_call(["screen", "-x", self.session, "-X", "register", "S", s])
                rv |= silent_call(["screen", "-x", self.session, "-X", "paste", "S"])
            else:
                rv |= silent_call(["screen", "-x", self.session, "-X", "stuff", s])
            if not rv: break
            time.sleep(.2)

    def detect_parsing(self):
        self.send(""" vim -u NONE\r\n""")  # Space to exclude from shell history
        time.sleep(1)

        # Send a string where the interpretation will depend on version of screen
        string = "$TERM"
        self.send("i" + string + ESC)
        output = self.get_buffer_data()
        # If the output doesn't match the input, need to do additional escaping
        if output != string:
            self.need_screen_escapes = 1
        self.send(ESC + ":q!\n")

class VimInterfaceTmux(VimInterface):
    def __init__(self, session):
        self.session = session
        self._check_version()

    def send(self, s):
        # I did not find any documentation on what needs escaping when sending
        # to tmux, but it seems like this is all that is needed for now.
        s = s.replace(';', r'\;')

        if PYTHON3:
            s = s.encode("utf-8")
        silent_call(["tmux", "send-keys", "-t", self.session, "-l", s])

    def _check_version(self):
        stdout, _ = subprocess.Popen(["tmux", "-V"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if PYTHON3:
            stdout = stdout.decode("utf-8")
        m = re.match(r"tmux (\d+).(\d+)", stdout)
        if not m or not (int(m.group(1)), int(m.group(2))) >= (1, 9):
            raise RuntimeError("Need at least tmux 1.9, you have %s." % stdout.strip())

class VimInterfaceWindows(VimInterface):
    BRACES = re.compile("([}{])")
    WIN_ESCAPES = ["+", "^", "%", "~", "[", "]", "<", ">", "(", ")"]
    WIN_REPLACES = [
            (BS, "{BS}"),
            (ARR_L, "{LEFT}"),
            (ARR_R, "{RIGHT}"),
            (ARR_U, "{UP}"),
            (ARR_D, "{DOWN}"),
            ("\t", "{TAB}"),
            ("\n", "~"),
            (ESC, "{ESC}"),

            # On my system ` waits for a second keystroke, so `+SPACE = "`".  On
            # most systems, `+Space = "` ". I work around this, by sending the host
            # ` as `+_+BS. Awkward, but the only way I found to get this working.
            ("`", "`_{BS}"),
            ("´", "´_{BS}"),
            ("{^}", "{^}_{BS}"),
    ]

    def __init__(self):
        self.seq_buf = []
        # import windows specific modules
        import win32com.client, win32gui
        self.win32gui = win32gui
        self.shell = win32com.client.Dispatch("WScript.Shell")

    def is_focused(self, title=None):
        cur_title = self.win32gui.GetWindowText(self.win32gui.GetForegroundWindow())
        if (title or "- GVIM") in cur_title:
            return True
        return False

    def focus(self, title=None):
        if not self.shell.AppActivate(title or "- GVIM"):
            raise Exception("Failed to switch to GVim window")
        time.sleep(1)

    def convert_keys(self, keys):
        keys = self.BRACES.sub(r"{\1}", keys)
        for k in self.WIN_ESCAPES:
            keys = keys.replace(k, "{%s}" % k)
        for f, r in self.WIN_REPLACES:
            keys = keys.replace(f, r)
        return keys

    def send(self, keys):
        self.seq_buf.append(keys)
        seq = "".join(self.seq_buf)

        for f in SEQUENCES:
            if f.startswith(seq) and f != seq:
                return
        self.seq_buf = []

        seq = self.convert_keys(seq)

        if not self.is_focused():
            time.sleep(2)
            self.focus()
        if not self.is_focused():
            # This is the only way I can find to stop test execution
            raise KeyboardInterrupt("Failed to focus GVIM")

        self.shell.SendKeys(seq)

def create_temp_file(prefix, suffix, content):
    """Create a file in a temporary place with the given 'prefix'
    and the given 'suffix' containing 'content'. The file is never
    deleted. Returns the name of the temporary file."""
    with tempfile.NamedTemporaryFile(
        prefix=prefix, suffix=suffix, delete=False
    ) as temporary_file:
        if PYTHON3:
            s = s.encode("utf-8")
        temporary_file.write(content)
        temporary_file.close()
        return temporary_file.name

class _VimTest(unittest.TestCase):
    snippets = ()
    files = {}
    text_before = " --- some text before --- \n\n"
    text_after =  "\n\n --- some text after --- "
    expected_error = ""
    wanted = ""
    keys = ""
    sleeptime = 0.00
    output = ""
    plugins = []
    # Skip this test for the given reason or None for not skipping it.
    skip_if = lambda self: None
    version = None  # Will be set to vim --version output

    def runTest(self):
        # Only checks the output. All work is done in setUp().
        wanted = self.text_before + self.wanted + self.text_after
        if self.expected_error:
            self.assertRegexpMatches(self.output, self.expected_error)
            return
        for i in range(self.retries):
            if self.output != wanted:
                # Redo this, but slower
                self.sleeptime += 0.02
                self.tearDown()
                self.setUp()
        self.assertEqual(self.output, wanted)

    def _extra_options_pre_init(self, vim_config):
        """Adds extra lines to the vim_config list."""

    def _extra_options_post_init(self, vim_config):
        """Adds extra lines to the vim_config list."""

    def _before_test(self):
        """Send these keys before the test runs. Used for buffer local
        variables and other options."""
        return ""

    def _create_file(self, file_path, content):
        """Creates a file in the runtimepath that is created for this test.
        Returns the absolute path to the file."""
        abs_path = os.path.join(self._temporary_directory, *file_path.split("/"))
        create_directory(os.path.dirname(abs_path))

        content = dedent(content + "\n")
        if PYTHON3:
            with open(abs_path, "w", encoding="utf-8") as file_handle:
                file_handle.write(content)
        else:
            with open(abs_path, "w") as file_handle:
                file_handle.write(content)
        return abs_path

    def _link_file(self, source, relative_destination):
        """Creates a link from 'source' to the 'relative_destination' in our temp dir."""
        absdir = os.path.join(self._temporary_directory, relative_destination)
        create_directory(absdir)
        os.symlink(source, os.path.join(absdir, os.path.basename(source)))

    def setUp(self):
        if not _VimTest.version:
            _VimTest.version, _ = subprocess.Popen(["vim", "--version"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            if PYTHON3:
                _VimTest.version = _VimTest.version.decode("utf-8")

        if self.plugins and not self.test_plugins:
            return self.skipTest("Not testing integration with other plugins.")
        reason_for_skipping = self.skip_if()
        if reason_for_skipping is not None:
            return self.skipTest(reason_for_skipping)

        self._temporary_directory = tempfile.mkdtemp(prefix="UltiSnips_Test")

        vim_config = []
        vim_config.append('set nocompatible')
        vim_config.append('set runtimepath=$VIMRUNTIME,.,%s' % self._temporary_directory)

        if self.plugins:
            self._link_file(os.path.join(plugin_cache_dir(), "vim-pathogen", "autoload"), ".")
            for plugin in self.plugins:
                self._link_file(os.path.join(plugin_cache_dir(), os.path.basename(plugin)), "bundle")
            vim_config.append("execute pathogen#infect()")

        # Vim parameters.
        vim_config.append('syntax on')
        vim_config.append('filetype plugin indent on')
        vim_config.append('set clipboard=""')
        vim_config.append('set encoding=utf-8')
        vim_config.append('set fileencoding=utf-8')
        vim_config.append('set buftype=nofile')
        vim_config.append('set shortmess=at')
        vim_config.append('let g:UltiSnipsExpandTrigger="<tab>"')
        vim_config.append('let g:UltiSnipsJumpForwardTrigger="?"')
        vim_config.append('let g:UltiSnipsJumpBackwardTrigger="+"')
        vim_config.append('let g:UltiSnipsListSnippets="@"')
        vim_config.append('let g:UltiSnipsUsePythonVersion="%i"' % (3 if PYTHON3 else 2))
        vim_config.append('let g:UltiSnipsSnippetDirectories=["us"]')

        self._extra_options_pre_init(vim_config)

        # Now activate UltiSnips.
        vim_config.append('call UltiSnips#bootstrap#Bootstrap()')

        self._extra_options_post_init(vim_config)

        # Finally, add the snippets and some configuration for the test.
        vim_config.append("%s << EOF" % ("py3" if PYTHON3 else "py"))

        if len(self.snippets) and not isinstance(self.snippets[0],tuple):
            self.snippets = ( self.snippets, )
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
            vim_config.append("UltiSnips_Manager.add_snippet(%r, %r, %r, %r, priority=%i)" % (
                    sv, content, description, options, priority))

        # fill buffer with default text and place cursor in between.
        prefilled_text = (self.text_before + self.text_after).splitlines()
        vim_config.append("vim.current.buffer[:] = %r\n" % prefilled_text)
        vim_config.append("vim.current.window.cursor = (max(len(vim.current.buffer)//2, 1), 0)")

        # Create a file to signalize to the test runner that we are done with starting Vim.
        vim_pid_file = os.path.join(self._temporary_directory, "vim.pid")
        done_file = os.path.join(self._temporary_directory, "loading_done")
        vim_config.append("with open('%s', 'w') as pid_file: pid_file.write(vim.eval('getpid()'))" %
                vim_pid_file)
        vim_config.append("with open('%s', 'w') as done_file: pass" % done_file)

        # End of python stuff.
        vim_config.append("EOF")

        for name, content in self.files.items():
            self._create_file(name, content)

        # Now launch Vim.
        self._create_file("vim_config.vim", os.linesep.join(vim_config))
        # Note the shell to exclude it from shell history.
        self.vim.send(""" vim -u %s\r\n""" % os.path.join(
            self._temporary_directory, "vim_config.vim"))
        while True:
            if os.path.exists(done_file):
                self._vim_pid = int(open(vim_pid_file, "r").read())
                break
            time.sleep(.01)

        self._before_test()

        if not self.interrupt:
            # Go into insert mode and type the keys but leave Vim some time to
            # react.
            for c in 'i' + self.keys:
                self.vim.send(c)
                time.sleep(self.sleeptime)
            self.output = self.vim.get_buffer_data()

    def tearDown(self):
        if self.interrupt:
            print("Working directory: %s" % (self._temporary_directory))
            return
        shutil.rmtree(self._temporary_directory)
        self.vim.send(3*ESC + ":qa!\n")
        while is_process_running(self._vim_pid):
            time.sleep(.05)

###########################################################################
#                            BEGINNING OF TEST                            #
###########################################################################
# Snippet Definition Parsing  {{{#
class ParseSnippets_SimpleSnippet(_VimTest):
    files = { "us/all.snippets": r"""
        snippet testsnip "Test Snippet" b!
        This is a test snippet!
        endsnippet
        """}
    keys = "testsnip" + EX
    wanted = "This is a test snippet!"

class ParseSnippets_MissingEndSnippet(_VimTest):
    files = { "us/all.snippets": r"""
        snippet testsnip "Test Snippet" b!
        This is a test snippet!
        """}
    keys = "testsnip" + EX
    wanted = "testsnip" + EX
    expected_error = r"Missing 'endsnippet' for 'testsnip' in \S+:4"

class ParseSnippets_UnknownDirective(_VimTest):
    files = { "us/all.snippets": r"""
        unknown directive
        """}
    keys = "testsnip" + EX
    wanted = "testsnip" + EX
    expected_error = r"Invalid line 'unknown directive' in \S+:2"

class ParseSnippets_InvalidPriorityLine(_VimTest):
    files = { "us/all.snippets": r"""
        priority - 50
        """}
    keys = "testsnip" + EX
    wanted = "testsnip" + EX
    expected_error = r"Invalid priority '- 50' in \S+:2"

class ParseSnippets_InvalidPriorityLine1(_VimTest):
    files = { "us/all.snippets": r"""
        priority
        """}
    keys = "testsnip" + EX
    wanted = "testsnip" + EX
    expected_error = r"Invalid priority '' in \S+:2"

class ParseSnippets_ExtendsWithoutFiletype(_VimTest):
    files = { "us/all.snippets": r"""
        extends
        """}
    keys = "testsnip" + EX
    wanted = "testsnip" + EX
    expected_error = r"'extends' without file types in \S+:2"

class ParseSnippets_ClearAll(_VimTest):
    files = { "us/all.snippets": r"""
        snippet testsnip "Test snippet"
        This is a test.
        endsnippet

        clearsnippets
        """}
    keys = "testsnip" + EX
    wanted = "testsnip" + EX

class ParseSnippets_ClearOne(_VimTest):
    files = { "us/all.snippets": r"""
        snippet testsnip "Test snippet"
        This is a test.
        endsnippet

        snippet toclear "Snippet to clear"
        Do not expand.
        endsnippet

        clearsnippets toclear
        """}
    keys = "toclear" + EX + "\n" + "testsnip" + EX
    wanted = "toclear" + EX + "\n" + "This is a test."

class ParseSnippets_ClearTwo(_VimTest):
    files = { "us/all.snippets": r"""
        snippet testsnip "Test snippet"
        This is a test.
        endsnippet

        snippet toclear "Snippet to clear"
        Do not expand.
        endsnippet

        clearsnippets testsnip toclear
        """}
    keys = "toclear" + EX + "\n" + "testsnip" + EX
    wanted = "toclear" + EX + "\n" + "testsnip" + EX


class _ParseSnippets_MultiWord(_VimTest):
    files = { "us/all.snippets": r"""
        snippet /test snip/
        This is a test.
        endsnippet

        snippet !snip test! "Another snippet"
        This is another test.
        endsnippet

        snippet "snippet test" "Another snippet" b
        This is yet another test.
        endsnippet
        """}
class ParseSnippets_MultiWord_Simple(_ParseSnippets_MultiWord):
    keys = "test snip" + EX
    wanted = "This is a test."
class ParseSnippets_MultiWord_Description(_ParseSnippets_MultiWord):
    keys = "snip test" + EX
    wanted = "This is another test."
class ParseSnippets_MultiWord_Description_Option(_ParseSnippets_MultiWord):
    keys = "snippet test" + EX
    wanted = "This is yet another test."

class _ParseSnippets_MultiWord_RE(_VimTest):
    files = { "us/all.snippets": r"""
        snippet /[d-f]+/ "" r
        az test
        endsnippet

        snippet !^(foo|bar)$! "" r
        foo-bar test
        endsnippet

        snippet "(test ?)+" "" r
        re-test
        endsnippet
        """}
class ParseSnippets_MultiWord_RE1(_ParseSnippets_MultiWord_RE):
    keys = "abc def" + EX
    wanted = "abc az test"
class ParseSnippets_MultiWord_RE2(_ParseSnippets_MultiWord_RE):
    keys = "foo" + EX + " bar" + EX + "\nbar" + EX
    wanted = "foo-bar test bar\t\nfoo-bar test"
class ParseSnippets_MultiWord_RE3(_ParseSnippets_MultiWord_RE):
    keys = "test test test" + EX
    wanted = "re-test"

class ParseSnippets_MultiWord_Quotes(_VimTest):
    files = { "us/all.snippets": r"""
        snippet "test snip"
        This is a test.
        endsnippet
        """}
    keys = "test snip" + EX
    wanted = "This is a test."
class ParseSnippets_MultiWord_WithQuotes(_VimTest):
    files = { "us/all.snippets": r"""
        snippet !"test snip"!
        This is a test.
        endsnippet
        """}
    keys = '"test snip"' + EX
    wanted = "This is a test."

class ParseSnippets_MultiWord_NoContainer(_VimTest):
    files = { "us/all.snippets": r"""
        snippet test snip
        This is a test.
        endsnippet
        """}
    keys = "test snip" + EX
    wanted = keys
    expected_error = "Invalid multiword trigger: 'test snip' in \S+:2"

class ParseSnippets_MultiWord_UnmatchedContainer(_VimTest):
    files = { "us/all.snippets": r"""
        snippet !inv snip/
        This is a test.
        endsnippet
        """}
    keys = "inv snip" + EX
    wanted = keys
    expected_error = "Invalid multiword trigger: '!inv snip/' in \S+:2"

class ParseSnippets_Global_Python(_VimTest):
    files = { "us/all.snippets": r"""
        global !p
        def tex(ins):
            return "a " + ins + " b"
        endglobal

        snippet ab
        x `!p snip.rv = tex("bob")` y
        endsnippet

        snippet ac
        x `!p snip.rv = tex("jon")` y
        endsnippet
        """}
    keys = "ab" + EX + "\nac" + EX
    wanted = "x a bob b y\nx a jon b y"

class ParseSnippets_Global_Local_Python(_VimTest):
    files = { "us/all.snippets": r"""
global !p
def tex(ins):
    return "a " + ins + " b"
endglobal

snippet ab
x `!p first = tex("bob")
snip.rv = "first"` `!p snip.rv = first` y
endsnippet
        """}
    keys = "ab" + EX
    wanted = "x first a bob b y"
# End: Snippet Definition Parsing  #}}}

# Simple Expands  {{{#
class _SimpleExpands(_VimTest):
    snippets = ("hallo", "Hallo Welt!")

class SimpleExpand_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX
    wanted = "Hallo Welt!"
class SimpleExpandTwice_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + '\nhallo' + EX
    wanted = "Hallo Welt!\nHallo Welt!"

class SimpleExpandNewLineAndBackspae_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + "\nHallo Welt!\n\n\b\b\b\b\b"
    wanted = "Hallo Welt!\nHallo We"
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set backspace=eol,start")

class SimpleExpandTypeAfterExpand_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo" + EX + "and again"
    wanted = "Hallo Welt!and again"

class SimpleExpandTypeAndDelete_ExpectCorrectResult(_SimpleExpands):
    keys = "na du hallo" + EX + "and again\b\b\b\b\bblub"
    wanted = "na du Hallo Welt!and blub"

class DoNotExpandAfterSpace_ExpectCorrectResult(_SimpleExpands):
    keys = "hallo " + EX
    wanted = "hallo " + EX

class ExitSnippetModeAfterTabstopZero(_VimTest):
    snippets = ("test", "SimpleText")
    keys = "test" + EX + EX
    wanted = "SimpleText" + EX

class ExpandInTheMiddleOfLine_ExpectCorrectResult(_SimpleExpands):
    keys = "Wie hallo gehts" + ESC + "bhi" + EX
    wanted = "Wie Hallo Welt! gehts"
class MultilineExpand_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts")
    keys = "Wie hallo gehts" + ESC + "bhi" + EX
    wanted = "Wie Hallo Welt!\nUnd Wie gehts gehts"
class MultilineExpandTestTyping_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt!\nUnd Wie gehts")
    wanted = "Wie Hallo Welt!\nUnd Wie gehtsHuiui! gehts"
    keys = "Wie hallo gehts" + ESC + "bhi" + EX + "Huiui!"
class SimpleExpandEndingWithNewline_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo Welt\n")
    keys = "hallo" + EX + "\nAnd more"
    wanted = "Hallo Welt\n\nAnd more"


# End: Simple Expands  #}}}
# TabStop Tests  {{{#
class TabStopSimpleReplace_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} ${1:Beginning}")
    keys = "hallo" + EX + "na" + JF + "Du Nase"
    wanted = "hallo Du Nase na"
class TabStopSimpleReplaceZeroLengthTabstops_ExpectCorrectResult(_VimTest):
    snippets = ("test", r":latex:\`$1\`$0")
    keys = "test" + EX + "Hello" + JF + "World"
    wanted = ":latex:`Hello`World"
class TabStopSimpleReplaceReversed_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${1:End} ${0:Beginning}")
    keys = "hallo" + EX + "na" + JF + "Du Nase"
    wanted = "hallo na Du Nase"
class TabStopSimpleReplaceSurrounded_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${0:End} a small feed")
    keys = "hallo" + EX + "Nase"
    wanted = "hallo Nase a small feed"
class TabStopSimpleReplaceSurrounded1_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 a small feed")
    keys = "hallo" + EX + "Nase"
    wanted = "hallo Nase a small feed"
class TabStop_Exit_ExpectCorrectResult(_VimTest):
    snippets = ("echo", "$0 run")
    keys = "echo" + EX + "test"
    wanted = "test run"

class TabStopNoReplace_ExpectCorrectResult(_VimTest):
    snippets = ("echo", "echo ${1:Hallo}")
    keys = "echo" + EX
    wanted = "echo Hallo"

class TabStop_EscapingCharsBackticks(_VimTest):
    snippets = ("test", r"snip \` literal")
    keys = "test" + EX
    wanted = "snip ` literal"
class TabStop_EscapingCharsDollars(_VimTest):
    snippets = ("test", r"snip \$0 $$0 end")
    keys = "test" + EX + "hi"
    wanted = "snip $0 $hi end"
class TabStop_EscapingCharsDollars1(_VimTest):
    snippets = ("test", r"a\${1:literal}")
    keys = "test" + EX
    wanted = "a${1:literal}"
class TabStop_EscapingCharsDollars_BeginningOfLine(_VimTest):
    snippets = ("test", "\n\\${1:literal}")
    keys = "test" + EX
    wanted = "\n${1:literal}"
class TabStop_EscapingCharsDollars_BeginningOfDefinitionText(_VimTest):
    snippets = ("test", "\\${1:literal}")
    keys = "test" + EX
    wanted = "${1:literal}"
class TabStop_EscapingChars_Backslash(_VimTest):
    snippets = ("test", r"This \ is a backslash!")
    keys = "test" + EX
    wanted = "This \\ is a backslash!"
class TabStop_EscapingChars_Backslash2(_VimTest):
    snippets = ("test", r"This is a backslash \\ done")
    keys = "test" + EX
    wanted = r"This is a backslash \ done"
class TabStop_EscapingChars_Backslash3(_VimTest):
    snippets = ("test", r"These are two backslashes \\\\ done")
    keys = "test" + EX
    wanted = r"These are two backslashes \\ done"
class TabStop_EscapingChars_Backslash4(_VimTest):
    # Test for bug 746446
    snippets = ("test", r"\\$1{$2}")
    keys = "test" + EX + "hello" + JF + "world"
    wanted = r"\hello{world}"
class TabStop_EscapingChars_RealLife(_VimTest):
    snippets = ("test", r"usage: \`basename \$0\` ${1:args}")
    keys = "test" + EX + "[ -u -v -d ]"
    wanted = "usage: `basename $0` [ -u -v -d ]"

class TabStopEscapingWhenSelected_ECR(_VimTest):
    snippets = ("test", "snip ${1:default}")
    keys = "test" + EX + ESC + "0ihi"
    wanted = "hisnip default"
class TabStopEscapingWhenSelectedSingleCharTS_ECR(_VimTest):
    snippets = ("test", "snip ${1:i}")
    keys = "test" + EX + ESC + "0ihi"
    wanted = "hisnip i"
class TabStopEscapingWhenSelectedNoCharTS_ECR(_VimTest):
    snippets = ("test", "snip $1")
    keys = "test" + EX + ESC + "0ihi"
    wanted = "hisnip "

class TabStopWithOneChar_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "nothing ${1:i} hups")
    keys = "hallo" + EX + "ship"
    wanted = "nothing ship hups"

class TabStopTestJumping_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte ${1:Beginning}")
    keys = "hallo" + EX + JF + "Test" + JF + "Hi"
    wanted = "hallo Test mitte BeginningHi"
class TabStopTestJumping2_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = "hallo" + EX + JF + "Test" + JF + "Hi"
    wanted = "hallo Test Hi"
class TabStopTestJumpingRLExampleWithZeroTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "each_byte { |${1:byte}| $0 }")
    keys = "test" + EX + JF + "Blah"
    wanted = "each_byte { |byte| Blah }"

class TabStopTestJumpingDontJumpToEndIfThereIsTabZero_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0 $1")
    keys = "hallo" + EX + "Test" + JF + "Hi" + JF + JF + "du"
    wanted = "hallo Hi" + 2*JF + "du Test"

class TabStopTestBackwardJumping_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo ${2:End} mitte${1:Beginning}")
    keys = "hallo" + EX + "Somelengthy Text" + JF + "Hi" + JB + \
            "Lets replace it again" + JF + "Blah" + JF + JB*2 + JF
    wanted = "hallo Blah mitteLets replace it again" + JB*2 + JF
class TabStopTestBackwardJumping2_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $2 $1")
    keys = "hallo" + EX + "Somelengthy Text" + JF + "Hi" + JB + \
            "Lets replace it again" + JF + "Blah" + JF + JB*2 + JF
    wanted = "hallo Blah Lets replace it again" + JB*2 + JF

class TabStopTestMultilineExpand_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "hallo $0\nnice $1 work\n$3 $2\nSeem to work")
    keys ="test hallo World" + ESC + "02f i" + EX + "world" + JF + "try" + \
            JF + "test" + JF + "one more" + JF
    wanted = "test hallo one more" + JF + "\nnice world work\n" \
            "test try\nSeem to work World"

class TabStop_TSInDefaultTextRLExample_OverwriteNone_ECR(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX
    wanted = """<div id="some_id">\n  \n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteFirst_NoJumpBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + " blah" + JF + "Hallo"
    wanted = """<div blah>\n  Hallo\n</div>"""
class TabStop_TSInDefaultTextRLExample_DeleteFirst(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + BS + JF + "Hallo"
    wanted = """<div>\n  Hallo\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteFirstJumpBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3  $0\n</div>""")
    keys = "test" + EX + "Hi" + JF + "Hallo" + JB + "SomethingElse" + JF + \
            "Nupl" + JF + "Nox"
    wanted = """<divSomethingElse>\n  Nupl  Nox\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteSecond(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End"
    wanted = """<div id="no">\n  End\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteSecondTabBack(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3 $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End" + JB + "yes" + JF + "Begin" \
            + JF + "Hi"
    wanted = """<div id="yes">\n  Begin Hi\n</div>"""
class TabStop_TSInDefaultTextRLExample_OverwriteSecondTabBackTwice(_VimTest):
    snippets = ("test", """<div${1: id="${2:some_id}"}>\n  $3 $0\n</div>""")
    keys = "test" + EX + JF + "no" + JF + "End" + JB + "yes" + JB + \
            " allaway" + JF + "Third" + JF + "Last"
    wanted = """<div allaway>\n  Third Last\n</div>"""

class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecond(_VimTest):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "ups" + JF + "End"
    wanted = """haupsblEnd"""
class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteFirst(_VimTest):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + "ups" + JF + "End"
    wanted = """hupslEnd"""
class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecondJumpBackOverwrite(_VimTest):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "longertext" + JB + "overwrite" + JF + "End"
    wanted = """hoverwritelEnd"""
class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecondJumpBackAndForward0(_VimTest):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "longertext" + JB + JF + "overwrite" + JF + "End"
    wanted = """haoverwriteblEnd"""
class TabStop_TSInDefaultText_ZeroLengthNested_OverwriteSecondJumpBackAndForward1(_VimTest):
    snippets = ("test", """h${1:a$2b}l""")
    keys = "test" + EX + JF + "longertext" + JB + JF + JF + "End"
    wanted = """halongertextblEnd"""

class TabStop_TSInDefaultNested_OverwriteOneJumpBackToOther(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second ${3:third}}} $4")
    keys = "test" + EX + JF + "Hallo" + JF + "Ende"
    wanted = "hi this Hallo Ende"
class TabStop_TSInDefaultNested_OverwriteOneJumpToThird(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second ${3:third}}} $4")
    keys = "test" + EX + JF + JF + "Hallo" + JF + "Ende"
    wanted = "hi this second Hallo Ende"
class TabStop_TSInDefaultNested_OverwriteOneJumpAround(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second ${3:third}}} $4")
    keys = "test" + EX + JF + JF + "Hallo" + JB+JB + "Blah" + JF + "Ende"
    wanted = "hi Blah Ende"

class TabStop_TSInDefault_MirrorsOutside_DoNothing(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX
    wanted = "hi this second second"
class TabStop_TSInDefault_MirrorsOutside_OverwriteSecond(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX + JF + "Hallo"
    wanted = "hi this Hallo Hallo"
class TabStop_TSInDefault_MirrorsOutside_Overwrite0(_VimTest):
    snippets = ("test", "hi ${1:this ${2:second}} $2")
    keys = "test" + EX + "Hallo"
    wanted = "hi Hallo "
class TabStop_TSInDefault_MirrorsOutside_Overwrite1(_VimTest):
    snippets = ("test", "$1: ${1:'${2:second}'} $2")
    keys = "test" + EX + "Hallo"
    wanted = "Hallo: Hallo "
class TabStop_TSInDefault_MirrorsOutside_OverwriteSecond1(_VimTest):
    snippets = ("test", "$1: ${1:'${2:second}'} $2")
    keys = "test" + EX + JF + "Hallo"
    wanted = "'Hallo': 'Hallo' Hallo"
class TabStop_TSInDefault_MirrorsOutside_OverwriteFirstSwitchNumbers(_VimTest):
    snippets = ("test", "$2: ${2:'${1:second}'} $1")
    keys = "test" + EX + "Hallo"
    wanted = "'Hallo': 'Hallo' Hallo"
class TabStop_TSInDefault_MirrorsOutside_OverwriteFirst_RLExample(_VimTest):
    snippets = ("test", """`!p snip.rv = t[1].split('/')[-1].lower().strip("'")` = require(${1:'${2:sys}'})""")
    keys = "test" + EX + "WORLD" + JF + "End"
    wanted = "world = require(WORLD)End"
class TabStop_TSInDefault_MirrorsOutside_OverwriteSecond_RLExample(_VimTest):
    snippets = ("test", """`!p snip.rv = t[1].split('/')[-1].lower().strip("'")` = require(${1:'${2:sys}'})""")
    keys = "test" + EX + JF + "WORLD" + JF + "End"
    wanted = "world = require('WORLD')End"

class TabStop_Multiline_Leave(_VimTest):
    snippets = ("test", "hi ${1:first line\nsecond line} world" )
    keys = "test" + EX
    wanted = "hi first line\nsecond line world"
class TabStop_Multiline_Overwrite(_VimTest):
    snippets = ("test", "hi ${1:first line\nsecond line} world" )
    keys = "test" + EX + "Nothing"
    wanted = "hi Nothing world"
class TabStop_Multiline_MirrorInFront_Leave(_VimTest):
    snippets = ("test", "hi $1 ${1:first line\nsecond line} world" )
    keys = "test" + EX
    wanted = "hi first line\nsecond line first line\nsecond line world"
class TabStop_Multiline_MirrorInFront_Overwrite(_VimTest):
    snippets = ("test", "hi $1 ${1:first line\nsecond line} world" )
    keys = "test" + EX + "Nothing"
    wanted = "hi Nothing Nothing world"
class TabStop_Multiline_DelFirstOverwriteSecond_Overwrite(_VimTest):
    snippets = ("test", "hi $1 $2 ${1:first line\nsecond line} ${2:Hi} world" )
    keys = "test" + EX + BS + JF + "Nothing"
    wanted = "hi  Nothing  Nothing world"

class TabStopNavigatingInInsertModeSimple_ExpectCorrectResult(_VimTest):
    snippets = ("hallo", "Hallo ${1:WELT} ups")
    keys = "hallo" + EX + "haselnut" + 2*ARR_L + "hips" + JF + "end"
    wanted = "Hallo haselnhipsut upsend"
# End: TabStop Tests  #}}}
# ShellCode Interpolation  {{{#
class TabStop_Shell_SimpleExample(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "hi `echo hallo` you!")
    keys = "test" + EX + "and more"
    wanted = "hi hallo you!and more"
class TabStop_Shell_WithUmlauts(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "hi `echo höüäh` you!")
    keys = "test" + EX + "and more"
    wanted = "hi höüäh you!and more"
class TabStop_Shell_TextInNextLine(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "hi `echo hallo`\nWeiter")
    keys = "test" + EX + "and more"
    wanted = "hi hallo\nWeiterand more"
class TabStop_Shell_InDefValue_Leave(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "Hallo ${1:now `echo fromecho`} end")
    keys = "test" + EX + JF + "and more"
    wanted = "Hallo now fromecho endand more"
class TabStop_Shell_InDefValue_Overwrite(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", "Hallo ${1:now `echo fromecho`} end")
    keys = "test" + EX + "overwrite" + JF + "and more"
    wanted = "Hallo overwrite endand more"
class TabStop_Shell_TestEscapedChars_Overwrite(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", r"""`echo \`echo "\\$hi"\``""")
    keys = "test" + EX
    wanted = "$hi"
class TabStop_Shell_TestEscapedCharsAndShellVars_Overwrite(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", r"""`hi="blah"; echo \`echo "$hi"\``""")
    keys = "test" + EX
    wanted = "blah"

class TabStop_Shell_ShebangPython(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = ("test", """Hallo ${1:now `#!/usr/bin/env python
print "Hallo Welt"
`} end""")
    keys = "test" + EX + JF + "and more"
    wanted = "Hallo now Hallo Welt endand more"
# End: ShellCode Interpolation  #}}}
# VimScript Interpolation  {{{#
class TabStop_VimScriptInterpolation_SimpleExample(_VimTest):
    snippets = ("test", """hi `!v indent(".")` End""")
    keys = "    test" + EX
    wanted = "    hi 4 End"
# End: VimScript Interpolation  #}}}
# PythonCode Interpolation  {{{#
# Deprecated Implementation  {{{#
class PythonCodeOld_SimpleExample(_VimTest):
    snippets = ("test", """hi `!p res = "Hallo"` End""")
    keys = "test" + EX
    wanted = "hi Hallo End"
class PythonCodeOld_ReferencePlaceholderAfter(_VimTest):
    snippets = ("test", """${1:hi} `!p res = t[1]+".blah"` End""")
    keys = "test" + EX + "ho"
    wanted = "ho ho.blah End"
class PythonCodeOld_ReferencePlaceholderBefore(_VimTest):
    snippets = ("test", """`!p res = len(t[1])*"#"`\n${1:some text}""")
    keys = "test" + EX + "Hallo Welt"
    wanted = "##########\nHallo Welt"
class PythonCodeOld_TransformedBeforeMultiLine(_VimTest):
    snippets = ("test", """${1/.+/egal/m} ${1:`!p
res = "Hallo"`} End""")
    keys = "test" + EX
    wanted = "egal Hallo End"
class PythonCodeOld_IndentedMultiline(_VimTest):
    snippets = ("test", """start `!p a = 1
b = 2
if b > a:
    res = "b isbigger a"
else:
    res = "a isbigger b"` end""")
    keys = "    test" + EX
    wanted = "    start b isbigger a end"
# End: Deprecated Implementation  #}}}
# New Implementation  {{{#
class PythonCode_UseNewOverOld(_VimTest):
    snippets = ("test", """hi `!p res = "Old"
snip.rv = "New"` End""")
    keys = "test" + EX
    wanted = "hi New End"

class PythonCode_SimpleExample(_VimTest):
    snippets = ("test", """hi `!p snip.rv = "Hallo"` End""")
    keys = "test" + EX
    wanted = "hi Hallo End"

class PythonCode_SimpleExample_ReturnValueIsEmptyString(_VimTest):
    snippets = ("test", """hi`!p snip.rv = ""`End""")
    keys = "test" + EX
    wanted = "hiEnd"

class PythonCode_ReferencePlaceholder(_VimTest):
    snippets = ("test", """${1:hi} `!p snip.rv = t[1]+".blah"` End""")
    keys = "test" + EX + "ho"
    wanted = "ho ho.blah End"

class PythonCode_ReferencePlaceholderBefore(_VimTest):
    snippets = ("test", """`!p snip.rv = len(t[1])*"#"`\n${1:some text}""")
    keys = "test" + EX + "Hallo Welt"
    wanted = "##########\nHallo Welt"
class PythonCode_TransformedBeforeMultiLine(_VimTest):
    snippets = ("test", """${1/.+/egal/m} ${1:`!p
snip.rv = "Hallo"`} End""")
    keys = "test" + EX
    wanted = "egal Hallo End"
class PythonCode_MultilineIndented(_VimTest):
    snippets = ("test", """start `!p a = 1
b = 2
if b > a:
    snip.rv = "b isbigger a"
else:
    snip.rv = "a isbigger b"` end""")
    keys = "    test" + EX
    wanted = "    start b isbigger a end"

class PythonCode_SimpleAppend(_VimTest):
    snippets = ("test", """hi `!p snip.rv = "Hallo1"
snip += "Hallo2"` End""")
    keys = "test" + EX
    wanted = "hi Hallo1\nHallo2 End"

class PythonCode_MultiAppend(_VimTest):
    snippets = ("test", """hi `!p snip.rv = "Hallo1"
snip += "Hallo2"
snip += "Hallo3"` End""")
    keys = "test" + EX
    wanted = "hi Hallo1\nHallo2\nHallo3 End"

class PythonCode_MultiAppendSimpleIndent(_VimTest):
    snippets = ("test", """hi
`!p snip.rv="Hallo1"
snip += "Hallo2"
snip += "Hallo3"`
End""")
    keys = """
    test""" + EX
    wanted = """
    hi
    Hallo1
    Hallo2
    Hallo3
    End"""

class PythonCode_SimpleMkline(_VimTest):
    snippets = ("test", r"""hi
`!p snip.rv="Hallo1\n"
snip.rv += snip.mkline("Hallo2") + "\n"
snip.rv += snip.mkline("Hallo3")`
End""")
    keys = """
    test""" + EX
    wanted = """
    hi
    Hallo1
    Hallo2
    Hallo3
    End"""

class PythonCode_MultiAppendShift(_VimTest):
    snippets = ("test", r"""hi
`!p snip.rv="i1"
snip += "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 3
snip += "i3"`
End""")
    keys = """
	test""" + EX
    wanted = """
	hi
	i1
	i1
		i2
i0
			i3
	End"""

class PythonCode_MultiAppendShiftMethods(_VimTest):
    snippets = ("test", r"""hi
`!p snip.rv="i1\n"
snip.rv += snip.mkline("i1\n")
snip.shift(1)
snip.rv += snip.mkline("i2\n")
snip.unshift(2)
snip.rv += snip.mkline("i0\n")
snip.shift(3)
snip.rv += snip.mkline("i3")`
End""")
    keys = """
	test""" + EX
    wanted = """
	hi
	i1
	i1
		i2
i0
			i3
	End"""


class PythonCode_ResetIndent(_VimTest):
    snippets = ("test", r"""hi
`!p snip.rv="i1"
snip >> 1
snip += "i2"
snip.reset_indent()
snip += "i1"
snip << 1
snip += "i0"
snip.reset_indent()
snip += "i1"`
End""")
    keys = """
	test""" + EX
    wanted = """
	hi
	i1
		i2
	i1
i0
	i1
	End"""

class PythonCode_IndentEtSw(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set expandtab")
    snippets = ("test", r"""hi
`!p snip.rv = "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 1
snip += "i1"
`
End""")
    keys = """   test""" + EX
    wanted = """   hi
   i1
      i2
i0
   i1
   End"""

class PythonCode_IndentEtSwOffset(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set expandtab")
    snippets = ("test", r"""hi
`!p snip.rv = "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 1
snip += "i1"
`
End""")
    keys = """    test""" + EX
    wanted = """    hi
    i1
       i2
 i0
    i1
    End"""

class PythonCode_IndentNoetSwTs(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set ts=4")
    snippets = ("test", r"""hi
`!p snip.rv = "i1"
snip >> 1
snip += "i2"
snip << 2
snip += "i0"
snip >> 1
snip += "i1"
`
End""")
    keys = """   test""" + EX
    wanted = """   hi
   i1
\t  i2
i0
   i1
   End"""

# Test using 'opt'
class PythonCode_OptExists(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append('let g:UStest="yes"')
    snippets = ("test", r"""hi `!p snip.rv = snip.opt("g:UStest") or "no"` End""")
    keys = """test""" + EX
    wanted = """hi yes End"""

class PythonCode_OptNoExists(_VimTest):
    snippets = ("test", r"""hi `!p snip.rv = snip.opt("g:UStest") or "no"` End""")
    keys = """test""" + EX
    wanted = """hi no End"""

class PythonCode_IndentProblem(_VimTest):
    # A test case which is likely related to bug 719649
    snippets = ("test", r"""hi `!p
snip.rv = "World"
` End""")
    keys = " " * 8 + "test" + EX  # < 8 works.
    wanted = """        hi World End"""

class PythonCode_TrickyReferences(_VimTest):
    snippets = ("test", r"""${2:${1/.+/egal/}} ${1:$3} ${3:`!p snip.rv = "hi"`}""")
    keys = "ups test" + EX
    wanted = "ups egal hi hi"
# locals
class PythonCode_Locals(_VimTest):
    snippets = ("test", r"""hi `!p a = "test"
snip.rv = "nothing"` `!p snip.rv = a
` End""")
    keys = """test""" + EX
    wanted = """hi nothing test End"""

class PythonCode_LongerTextThanSource_Chars(_VimTest):
    snippets = ("test", r"""hi`!p snip.rv = "a" * 100`end""")
    keys = """test""" + EX + "ups"
    wanted = "hi" + 100*"a" + "endups"

class PythonCode_LongerTextThanSource_MultiLine(_VimTest):
    snippets = ("test", r"""hi`!p snip.rv = "a" * 100 + '\n'*100 + "a"*100`end""")
    keys = """test""" + EX + "ups"
    wanted = "hi" + 100*"a" + 100*"\n" + 100*"a" + "endups"

class PythonCode_AccessKilledTabstop_OverwriteSecond(_VimTest):
    snippets = ("test", r"`!p snip.rv = t[2].upper()`${1:h${2:welt}o}`!p snip.rv = t[2].upper()`")
    keys = "test" + EX + JF + "okay"
    wanted = "OKAYhokayoOKAY"
class PythonCode_AccessKilledTabstop_OverwriteFirst(_VimTest):
    snippets = ("test", r"`!p snip.rv = t[2].upper()`${1:h${2:welt}o}`!p snip.rv = t[2].upper()`")
    keys = "test" + EX + "aaa"
    wanted = "aaa"

class PythonVisual_NoVisualSelection_Ignore(_VimTest):
    snippets = ("test", "h`!p snip.rv = snip.v.mode + snip.v.text`b")
    keys = "test" + EX + "abc"
    wanted = "hbabc"
class PythonVisual_SelectOneWord(_VimTest):
    snippets = ("test", "h`!p snip.rv = snip.v.mode + snip.v.text`b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX
    wanted = "hvblablubb"
class PythonVisual_LineSelect_Simple(_VimTest):
    snippets = ("test", "h`!p snip.rv = snip.v.mode + snip.v.text`b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX
    wanted = "hVhello\nnice\nworld\nb"

# Tests for https://bugs.launchpad.net/bugs/1259349
class Python_WeirdScoping_Error(_VimTest):
    snippets = ("test", "h`!p import re; snip.rv = '%i' % len([re.search for i in 'aiiia'])`b")
    keys = "test" + EX
    wanted = "h5b"
# End: New Implementation  #}}}
# End: PythonCode Interpolation  #}}}
# Mirrors  {{{#
class TextTabStopTextAfterTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 Hinten\n$1")
    keys = "test" + EX + "hallo"
    wanted = "hallo Hinten\nhallo"
class TextTabStopTextBeforeTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1\n$1")
    keys = "test" + EX + "hallo"
    wanted = "Vorne hallo\nhallo"
class TextTabStopTextSurroundedTab_ExpectCorrectResult(_VimTest):
    snippets = ("test", "Vorne $1 Hinten\n$1")
    keys = "test" + EX + "hallo test"
    wanted = "Vorne hallo test Hinten\nhallo test"

class TextTabStopTextBeforeMirror_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nVorne hallo"
class TextTabStopAfterMirror_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1 Hinten")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nhallo Hinten"
class TextTabStopSurroundMirror_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\nVorne $1 Hinten")
    keys = "test" + EX + "hallo welt"
    wanted = "hallo welt\nVorne hallo welt Hinten"
class TextTabStopAllSurrounded_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ObenVorne $1 ObenHinten\nVorne $1 Hinten")
    keys = "test" + EX + "hallo welt"
    wanted = "ObenVorne hallo welt ObenHinten\nVorne hallo welt Hinten"

class MirrorBeforeTabstopLeave_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test" + EX
    wanted = "this is it this is it this is it"
class MirrorBeforeTabstopOverwrite_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1:this is it} $1")
    keys = "test" + EX + "a"
    wanted = "a a a"

class TextTabStopSimpleMirrorMultiline_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo"
    wanted = "hallo\nhallo"
class SimpleMirrorMultilineMany_ExpectCorrectResult(_VimTest):
    snippets = ("test", "    $1\n$1\na$1b\n$1\ntest $1 mich")
    keys = "test" + EX + "hallo"
    wanted = "    hallo\nhallo\nahallob\nhallo\ntest hallo mich"
class MultilineTabStopSimpleMirrorMultiline_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n\n$1\n\n$1")
    keys = "test" + EX + "hallo Du\nHi"
    wanted = "hallo Du\nHi\n\nhallo Du\nHi\n\nhallo Du\nHi"
class MultilineTabStopSimpleMirrorMultiline1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test" + EX + "hallo Du\nHi"
    wanted = "hallo Du\nHi\nhallo Du\nHi\nhallo Du\nHi"
class MultilineTabStopSimpleMirrorDeleteInLine_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1\n$1")
    keys = "test" + EX + "hallo Du\nHi\b\bAch Blah"
    wanted = "hallo Du\nAch Blah\nhallo Du\nAch Blah\nhallo Du\nAch Blah"
class TextTabStopSimpleMirrorMultilineMirrorInFront_ECR(_VimTest):
    snippets = ("test", "$1\n${1:sometext}")
    keys = "test" + EX + "hallo\nagain"
    wanted = "hallo\nagain\nhallo\nagain"

class SimpleMirrorDelete_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo\b\b"
    wanted = "hal\nhal"

class SimpleMirrorSameLine_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1")
    keys = "test" + EX + "hallo"
    wanted = "hallo hallo"
class SimpleMirrorSameLine_InText_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1")
    keys = "ups test blah" + ESC + "02f i" + EX + "hallo"
    wanted = "ups hallo hallo blah"
class SimpleMirrorSameLineBeforeTabDefVal_ECR(_VimTest):
    snippets = ("test", "$1 ${1:replace me}")
    keys = "test" + EX + "hallo foo"
    wanted = "hallo foo hallo foo"
class SimpleMirrorSameLineBeforeTabDefVal_DelB4Typing_ECR(_VimTest):
    snippets = ("test", "$1 ${1:replace me}")
    keys = "test" + EX + BS + "hallo foo"
    wanted = "hallo foo hallo foo"
class SimpleMirrorSameLineMany_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test" + EX + "hallo du"
    wanted = "hallo du hallo du hallo du hallo du"
class SimpleMirrorSameLineManyMultiline_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 $1 $1 $1")
    keys = "test" + EX + "hallo du\nwie gehts"
    wanted = "hallo du\nwie gehts hallo du\nwie gehts hallo du\nwie gehts" \
            " hallo du\nwie gehts"
class SimpleMirrorDeleteSomeEnterSome_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1\n$1")
    keys = "test" + EX + "hallo\b\bhups"
    wanted = "halhups\nhalhups"

class SimpleTabstopWithDefaultSimpelType_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test" + EX + "world"
    wanted = "ha world\nworld"
class SimpleTabstopWithDefaultComplexType_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test" + EX + "world"
    wanted = "ha world world\nanother: world mirror"
class SimpleTabstopWithDefaultSimpelKeep_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:defa}\n$1")
    keys = "test" + EX
    wanted = "ha defa\ndefa"
class SimpleTabstopWithDefaultComplexKeep_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:default value} $1\nanother: $1 mirror")
    keys = "test" + EX
    wanted = "ha default value default value\nanother: default value mirror"

class TabstopWithMirrorManyFromAll_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $5 ${1:blub} $4 $0 ${2:$1.h} $1 $3 ${4:More}")
    keys = "test" + EX + "hi" + JF + "hu" + JF + "hub" + JF + "hulla" + \
            JF + "blah" + JF + "end"
    wanted = "ha blah hi hulla end hu hi hub hulla"
class TabstopWithMirrorInDefaultNoType_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:blub} ${2:$1.h}")
    keys = "test" + EX
    wanted = "ha blub blub.h"
class TabstopWithMirrorInDefaultNoType1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha ${1:blub} ${2:$1}")
    keys = "test" + EX
    wanted = "ha blub blub"
class TabstopWithMirrorInDefaultTwiceAndExtra_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h $1.c}\ntest $1")
    keys = "test" + EX + "stdin"
    wanted = "ha stdin stdin.h stdin.c\ntest stdin"
class TabstopWithMirrorInDefaultMultipleLeave_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test" + EX + "stdin"
    wanted = "ha stdin snip stdin.h snip"
class TabstopWithMirrorInDefaultMultipleOverwrite_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:snip} ${3:$1.h $2}")
    keys = "test" + EX + "stdin" + JF + "do snap"
    wanted = "ha stdin do snap stdin.h do snap"
class TabstopWithMirrorInDefaultOverwrite_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1.h}")
    keys = "test" + EX + "stdin" + JF + "overwritten"
    wanted = "ha stdin overwritten"
class TabstopWithMirrorInDefaultOverwrite1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1}")
    keys = "test" + EX + "stdin" + JF + "overwritten"
    wanted = "ha stdin overwritten"
class TabstopWithMirrorInDefaultNoOverwrite1_ExpectCorrectResult(_VimTest):
    snippets = ("test", "ha $1 ${2:$1}")
    keys = "test" + EX + "stdin" + JF + JF + "end"
    wanted = "ha stdin stdinend"

class MirrorRealLifeExample_ExpectCorrectResult(_VimTest):
    snippets = (
        ("for", "for(size_t ${2:i} = 0; $2 < ${1:count}; ${3:++$2})" \
         "\n{\n\t${0:/* code */}\n}"),
    )
    keys ="for" + EX + "100" + JF + "avar\b\b\b\ba_variable" + JF + \
            "a_variable *= 2" + JF + "// do nothing"
    wanted = """for(size_t a_variable = 0; a_variable < 100; a_variable *= 2)
{
\t// do nothing
}"""

class Mirror_TestKill_InsertBefore_NoKill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "wihi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch hinoauch_end"
class Mirror_TestKill_InsertAfter_NoKill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "eiab" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch noauchab_end"
class Mirror_TestKill_InsertBeginning_Kill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "wahi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch ahiuch_end"
class Mirror_TestKill_InsertEnd_Kill(_VimTest):
    snippets = "test", "$1 $1_"
    keys = "hallo test" + EX + "auch" + ESC + "ehihi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noauch auchih_end"
class Mirror_TestKillTabstop_Kill(_VimTest):
    snippets = "test", "welt${1:welt${2:welt}welt} $2"
    keys = "hallo test" + EX + "elt"
    wanted = "hallo weltelt "

# End: Mirrors  #}}}
# Transformations  {{{#
class Transformation_SimpleCase_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    keys = "test" + EX + "hallo foo boy"
    wanted = "hallo foo boy hallo batzl boy"
class Transformation_SimpleCaseNoTransform_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/foo/batzl/}")
    keys = "test" + EX + "hallo"
    wanted = "hallo hallo"
class Transformation_SimpleCaseTransformInFront_ExpectCorrectResult(_VimTest):
    snippets = ("test", "${1/foo/batzl/} $1")
    keys = "test" + EX + "hallo foo"
    wanted = "hallo batzl hallo foo"
class Transformation_SimpleCaseTransformInFrontDefVal_ECR(_VimTest):
    snippets = ("test", "${1/foo/batzl/} ${1:replace me}")
    keys = "test" + EX + "hallo foo"
    wanted = "hallo batzl hallo foo"
class Transformation_MultipleTransformations_ECR(_VimTest):
    snippets = ("test", "${1:Some Text}${1/.+/\\U$0\E/}\n${1/.+/\L$0\E/}")
    keys = "test" + EX + "SomE tExt "
    wanted = "SomE tExt SOME TEXT \nsome text "
class Transformation_TabIsAtEndAndDeleted_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    keys = "hallo test" + EX + "some\b\b\b\b\b"
    wanted = "hallo "
class Transformation_TabIsAtEndAndDeleted1_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1:some}")
    keys = "hallo test" + EX + "some\b\b\b\bmore"
    wanted = "hallo is somethingmore"
class Transformation_TabIsAtEndNoTextLeave_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    keys = "hallo test" + EX
    wanted = "hallo "
class Transformation_TabIsAtEndNoTextType_ECR(_VimTest):
    snippets = ("test", "${1/.+/is something/}${1}")
    keys = "hallo test" + EX + "b"
    wanted = "hallo is somethingb"
class Transformation_InsideTabLeaveAtDefault_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:${1/.+/(?0:defined $0)/}}")
    keys = "test" + EX + "sometext" + JF
    wanted = "sometext defined sometext"
class Transformation_InsideTabOvertype_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:${1/.+/(?0:defined $0)/}}")
    keys = "test" + EX + "sometext" + JF + "overwrite"
    wanted = "sometext overwrite"


class Transformation_Backreference_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/([ab])oo/$1ull/}")
    keys = "test" + EX + "foo boo aoo"
    wanted = "foo boo aoo foo bull aoo"
class Transformation_BackreferenceTwice_ExpectCorrectResult(_VimTest):
    snippets = ("test", r"$1 ${1/(dead) (par[^ ]*)/this $2 is a bit $1/}")
    keys = "test" + EX + "dead parrot"
    wanted = "dead parrot this parrot is a bit dead"

class Transformation_CleverTransformUpercaseChar_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.)/\\u$1/}")
    keys = "test" + EX + "hallo"
    wanted = "hallo Hallo"
class Transformation_CleverTransformLowercaseChar_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\l$1/}")
    keys = "test" + EX + "Hallo"
    wanted = "Hallo hallo"
class Transformation_CleverTransformLongUpper_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\\U$1\E/}")
    keys = "test" + EX + "hallo"
    wanted = "hallo HALLO"
class Transformation_CleverTransformLongLower_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(.*)/\L$1\E/}")
    keys = "test" + EX + "HALLO"
    wanted = "HALLO hallo"

class Transformation_SimpleCaseAsciiResult(_VimTest):
    skip_if = lambda self: no_unidecode_available()
    snippets = ("ascii", "$1 ${1/(.*)/$1/a}")
    keys = "ascii" + EX + "éèàçôïÉÈÀÇÔÏ€"
    wanted = "éèàçôïÉÈÀÇÔÏ€ eeacoiEEACOIEU"
class Transformation_LowerCaseAsciiResult(_VimTest):
    skip_if = lambda self: no_unidecode_available()
    snippets = ("ascii", "$1 ${1/(.*)/\L$1\E/a}")
    keys = "ascii" + EX + "éèàçôïÉÈÀÇÔÏ€"
    wanted = "éèàçôïÉÈÀÇÔÏ€ eeacoieeacoieu"

class Transformation_ConditionalInsertionSimple_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(^a).*/(?0:began with an a)/}")
    keys = "test" + EX + "a some more text"
    wanted = "a some more text began with an a"
class Transformation_CIBothDefinedNegative_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    keys = "test" + EX + "b some"
    wanted = "b some no"
class Transformation_CIBothDefinedPositive_ExpectCorrectResult(_VimTest):
    snippets = ("test", "$1 ${1/(?:(^a)|(^b)).*/(?1:yes:no)/}")
    keys = "test" + EX + "a some"
    wanted = "a some yes"
class Transformation_ConditionalInsertRWEllipsis_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/(\w+(?:\W+\w+){,7})\W*(.+)?/$1(?2:...)/}")
    keys = "test" + EX + "a b  c d e f ghhh h oha"
    wanted = "a b  c d e f ghhh h oha a b  c d e f ghhh h..."
class Transformation_ConditionalInConditional_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/^.*?(-)?(>)?$/(?2::(?1:>:.))/}")
    keys = "test" + EX + "hallo" + ESC + "$a\n" + \
           "test" + EX + "hallo-" + ESC + "$a\n" + \
           "test" + EX + "hallo->"
    wanted = "hallo .\nhallo- >\nhallo-> "

class Transformation_CINewlines_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */\n/}")
    keys = "test" + EX + "test, hallo"
    wanted = "test, hallo test\nhallo"
class Transformation_CITabstop_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */\t/}")
    keys = "test" + EX + "test, hallo"
    wanted = "test, hallo test\thallo"
class Transformation_CIEscapedParensinReplace_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/hal((?:lo)|(?:ul))/(?1:ha\($1\))/}")
    keys = "test" + EX + "test, halul"
    wanted = "test, halul test, ha(ul)"

class Transformation_OptionIgnoreCase_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/test/blah/i}")
    keys = "test" + EX + "TEST"
    wanted = "TEST blah"
class Transformation_OptionReplaceGlobal_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */-/g}")
    keys = "test" + EX + "a, nice, building"
    wanted = "a, nice, building a-nice-building"
class Transformation_OptionReplaceGlobalMatchInReplace_ECR(_VimTest):
    snippets = ("test", r"$1 ${1/, */, /g}")
    keys = "test" + EX + "a, nice,   building"
    wanted = "a, nice,   building a, nice, building"
class TransformationUsingBackspaceToDeleteDefaultValueInFirstTab_ECR(_VimTest):
     snippets = ("test", "snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} "
                 "${1:default} ${2:def}")
     keys = "test" + EX + BS + JF + "hi"
     wanted = "snip  m2  hi"
class TransformationUsingBackspaceToDeleteDefaultValueInSecondTab_ECR(_VimTest):
     snippets = ("test", "snip ${1/.+/(?0:m1)/} ${2/.+/(?0:m2)/} "
                 "${1:default} ${2:def}")
     keys = "test" + EX + "hi" + JF + BS
     wanted = "snip m1  hi "
class TransformationUsingBackspaceToDeleteDefaultValueTypeSomethingThen_ECR(_VimTest):
     snippets = ("test", "snip ${1/.+/(?0:matched)/} ${1:default}")
     keys = "test" + EX + BS + "hallo"
     wanted = "snip matched hallo"
class TransformationUsingBackspaceToDeleteDefaultValue_ECR(_VimTest):
     snippets = ("test", "snip ${1/.+/(?0:matched)/} ${1:default}")
     keys = "test" + EX + BS
     wanted = "snip  "
class Transformation_TestKill_InsertBefore_NoKill(_VimTest):
    snippets = "test", r"$1 ${1/.*/\L$0$0\E/}_"
    keys = "hallo test" + EX + "AUCH" + ESC + "wihi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noAUCH hinoauchnoauch_end"
class Transformation_TestKill_InsertAfter_NoKill(_VimTest):
    snippets = "test", r"$1 ${1/.*/\L$0$0\E/}_"
    keys = "hallo test" + EX + "AUCH" + ESC + "eiab" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noAUCH noauchnoauchab_end"
class Transformation_TestKill_InsertBeginning_Kill(_VimTest):
    snippets = "test", r"$1 ${1/.*/\L$0$0\E/}_"
    keys = "hallo test" + EX + "AUCH" + ESC + "wahi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noAUCH ahiuchauch_end"
class Transformation_TestKill_InsertEnd_Kill(_VimTest):
    snippets = "test", r"$1 ${1/.*/\L$0$0\E/}_"
    keys = "hallo test" + EX + "AUCH" + ESC + "ehihi" + ESC + "bb" + "ino" + JF + "end"
    wanted = "hallo noAUCH auchauchih_end"
# End: Transformations  #}}}
# ${VISUAL}  {{{#
class Visual_NoVisualSelection_Ignore(_VimTest):
    snippets = ("test", "h${VISUAL}b")
    keys = "test" + EX + "abc"
    wanted = "hbabc"
class Visual_SelectOneWord(_VimTest):
    snippets = ("test", "h${VISUAL}b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX
    wanted = "hblablubb"
class Visual_SelectOneWord_ProblemAfterTab(_VimTest):
    snippets = ("test", "h${VISUAL}b", "", "i")
    keys = "\tblablub" + ESC + "5hv3l" + EX + "test" + EX
    wanted = "\tbhlablbub"
class VisualWithDefault_ExpandWithoutVisual(_VimTest):
    snippets = ("test", "h${VISUAL:world}b")
    keys = "test" + EX + "hi"
    wanted = "hworldbhi"
class VisualWithDefaultWithSlashes_ExpandWithoutVisual(_VimTest):
    snippets = ("test", r"h${VISUAL:\/\/ body}b")
    keys = "test" + EX + "hi"
    wanted = "h// bodybhi"
class VisualWithDefault_ExpandWithVisual(_VimTest):
    snippets = ("test", "h${VISUAL:world}b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX
    wanted = "hblablubb"

class Visual_ExpandTwice(_VimTest):
    snippets = ("test", "h${VISUAL}b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX + "\ntest" + EX
    wanted = "hblablubb\nhb"

class Visual_SelectOneWord_TwiceVisual(_VimTest):
    snippets = ("test", "h${VISUAL}b${VISUAL}a")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX
    wanted = "hblablubbblabluba"
class Visual_SelectOneWord_Inword(_VimTest):
    snippets = ("test", "h${VISUAL}b", "Description", "i")
    keys = "blablub" + ESC + "0lv4l" + EX + "test" + EX
    wanted = "bhlablubb"
class Visual_SelectOneWord_TillEndOfLine(_VimTest):
    snippets = ("test", "h${VISUAL}b", "Description", "i")
    keys = "blablub" + ESC + "0v$" + EX + "test" + EX + ESC + "o"
    wanted = "hblablub\nb"
class Visual_SelectOneWordWithTabstop_TillEndOfLine(_VimTest):
    snippets = ("test", "h${2:ahh}${VISUAL}${1:ups}b", "Description", "i")
    keys = "blablub" + ESC + "0v$" + EX + "test" + EX + "mmm" + JF + "n" + JF + "done" + ESC + "o"
    wanted = "hnblablub\nmmmbdone"
class Visual_InDefaultText_SelectOneWord_NoOverwrite(_VimTest):
    snippets = ("test", "h${1:${VISUAL}}b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX + JF + "hello"
    wanted = "hblablubbhello"
class Visual_InDefaultText_SelectOneWord(_VimTest):
    snippets = ("test", "h${1:${VISUAL}}b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX + "hello"
    wanted = "hhellob"

class Visual_CrossOneLine(_VimTest):
    snippets = ("test", "h${VISUAL}b")
    keys = "bla blub\n  helloi" + ESC + "0k4lvjll" + EX + "test" + EX
    wanted = "bla hblub\n  hellobi"

class Visual_LineSelect_Simple(_VimTest):
    snippets = ("test", "h${VISUAL}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX
    wanted = "hhello\n nice\n worldb"
class Visual_InDefaultText_LineSelect_NoOverwrite(_VimTest):
    snippets = ("test", "h${1:bef${VISUAL}aft}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + JF + "hi"
    wanted = "hbefhello\n    nice\n    worldaftbhi"
class Visual_InDefaultText_LineSelect_Overwrite(_VimTest):
    snippets = ("test", "h${1:bef${VISUAL}aft}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + "jup" + JF + "hi"
    wanted = "hjupbhi"
class Visual_LineSelect_CheckIndentSimple(_VimTest):
    snippets = ("test", "beg\n\t${VISUAL}\nend")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX
    wanted = "beg\n\thello\n\tnice\n\tworld\nend"
class Visual_LineSelect_CheckIndentTwice(_VimTest):
    snippets = ("test", "beg\n\t${VISUAL}\nend")
    keys = "    hello\n    nice\n\tworld" + ESC + "Vkk" + EX + "test" + EX
    wanted = "beg\n\t    hello\n\t    nice\n\t\tworld\nend"
class Visual_InDefaultText_IndentSpacesToTabstop_NoOverwrite(_VimTest):
    snippets = ("test", "h${1:beforea${VISUAL}aft}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + JF + "hi"
    wanted = "hbeforeahello\n\tnice\n\tworldaftbhi"
class Visual_InDefaultText_IndentSpacesToTabstop_Overwrite(_VimTest):
    snippets = ("test", "h${1:beforea${VISUAL}aft}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + "ups" + JF + "hi"
    wanted = "hupsbhi"
class Visual_InDefaultText_IndentSpacesToTabstop_NoOverwrite1(_VimTest):
    snippets = ("test", "h${1:beforeaaa${VISUAL}aft}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + JF + "hi"
    wanted = "hbeforeaaahello\n\t  nice\n\t  worldaftbhi"
class Visual_InDefaultText_IndentBeforeTabstop_NoOverwrite(_VimTest):
    snippets = ("test", "hello\n\t ${1:${VISUAL}}\nend")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + JF + "hi"
    wanted = "hello\n\t hello\n\t nice\n\t world\nendhi"

class Visual_LineSelect_WithTabStop(_VimTest):
    snippets = ("test", "beg\n\t${VISUAL}\n\t${1:here_we_go}\nend")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + "super" + JF + "done"
    wanted = "beg\n\thello\n\tnice\n\tworld\n\tsuper\nenddone"
class Visual_LineSelect_CheckIndentWithTS_NoOverwrite(_VimTest):
    snippets = ("test", "beg\n\t${0:${VISUAL}}\nend")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX
    wanted = "beg\n\thello\n\tnice\n\tworld\nend"
class Visual_LineSelect_DedentLine(_VimTest):
    snippets = ("if", "if {\n\t${VISUAL}$0\n}")
    keys = "if" + EX + "one\n\ttwo\n\tthree" + ESC + ARR_U*2 + "V" + ARR_D + EX + "\tif" + EX
    wanted = "if {\n\tif {\n\t\tone\n\t\ttwo\n\t}\n\tthree\n}"

class VisualTransformation_SelectOneWord(_VimTest):
    snippets = ("test", r"h${VISUAL/./\U$0\E/g}b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX
    wanted = "hBLABLUBb"
class VisualTransformationWithDefault_ExpandWithoutVisual(_VimTest):
    snippets = ("test", r"h${VISUAL:world/./\U$0\E/g}b")
    keys = "test" + EX + "hi"
    wanted = "hWORLDbhi"
class VisualTransformationWithDefault_ExpandWithVisual(_VimTest):
    snippets = ("test", r"h${VISUAL:world/./\U$0\E/g}b")
    keys = "blablub" + ESC + "0v6l" + EX + "test" + EX
    wanted = "hBLABLUBb"
class VisualTransformation_LineSelect_Simple(_VimTest):
    snippets = ("test", r"h${VISUAL/./\U$0\E/g}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX
    wanted = "hHELLO\n NICE\n WORLDb"
class VisualTransformation_InDefaultText_LineSelect_NoOverwrite(_VimTest):
    snippets = ("test", r"h${1:bef${VISUAL/./\U$0\E/g}aft}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + JF + "hi"
    wanted = "hbefHELLO\n    NICE\n    WORLDaftbhi"
class VisualTransformation_InDefaultText_LineSelect_Overwrite(_VimTest):
    snippets = ("test", r"h${1:bef${VISUAL/./\U$0\E/g}aft}b")
    keys = "hello\nnice\nworld" + ESC + "Vkk" + EX + "test" + EX + "jup" + JF + "hi"
    wanted = "hjupbhi"

# End: ${VISUAL}  #}}}

# Recursive (Nested) Snippets  {{{#
class RecTabStops_SimpleCase_ExpectCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "m" + EX + "hello" + JF + "world" + JF + "ups" + JF + "end"
    wanted = "[ [ hello  world ]ups  end ]"
class RecTabStops_SimpleCaseLeaveSecondSecond_ExpectCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "m" + EX + "hello" + JF + "world" + JF + JF + JF + "end"
    wanted = "[ [ hello  world ]  sec ]end"
class RecTabStops_SimpleCaseLeaveFirstSecond_ExpectCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "m" + EX + "hello" + JF + JF + JF + "world" + JF + "end"
    wanted = "[ [ hello  sec ]  world ]end"

class RecTabStops_InnerWOTabStop_ECR(_VimTest):
    snippets = (
        ("m1", "Just some Text"),
        ("m", "[ ${1:first}  ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + "hi" + JF + "two" + JF + "end"
    wanted = "[ Just some Texthi  two ]end"
class RecTabStops_InnerWOTabStopTwiceDirectly_ECR(_VimTest):
    snippets = (
        ("m1", "JST"),
        ("m", "[ ${1:first}  ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + " m1" + EX + "hi" + JF + "two" + JF + "end"
    wanted = "[ JST JSThi  two ]end"
class RecTabStops_InnerWOTabStopTwice_ECR(_VimTest):
    snippets = (
        ("m1", "JST"),
        ("m", "[ ${1:first}  ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + JF + "m1" + EX + "hi" + JF + "end"
    wanted = "[ JST  JSThi ]end"
class RecTabStops_OuterOnlyWithZeroTS_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "m1" + EX + "CD" + JF + "DE"
    wanted = "A C CD D DE E B"
class RecTabStops_OuterOnlyWithZero_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "m1" + EX + "CD" + JF + "DE"
    wanted = "A C CD D DE E B"
class RecTabStops_ExpandedInZeroTS_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B $1"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "hi" + JF + "m1" + EX + "CD" + JF + "DE"
    wanted = "A C CD D DE E B hi"
class RecTabStops_ExpandedInZeroTSTwice_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B $1"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "hi" + JF + "m" + EX + "again" + JF + "m1" + \
            EX + "CD" + JF + "DE"
    wanted = "A A C CD D DE E B again B hi"
class RecTabStops_ExpandedInZeroTSSecondTime_ECR(_VimTest):
    snippets = (
        ("m", "A $0 B $1"),
        ("m1", "C $1 D $0 E"),
    )
    keys = "m" + EX + "hi" + JF + "m" + EX + "m1" + EX + "CD" + JF + "DE" + JF + "AB"
    wanted = "A A AB B C CD D DE E B hi"
class RecTabsStops_TypeInZero_ECR(_VimTest):
    snippets = (
        ("v", r"\vec{$1}", "Vector", "w"),
        ("frac", r"\frac{${1:one}}${0:zero}{${2:two}}", "Fractio", "w"),
    )
    keys = "v" + EX + "frac" + EX + "a" + JF + "b" + JF + "frac" + EX + "aa" + JF + JF + "cc" + JF + \
            "hello frac" + EX + JF + JF + "world"
    wanted = r"\vec{\frac{a}\frac{aa}cc{two}{b}}hello \frac{one}world{two}"
class RecTabsStops_TypeInZero2_ECR(_VimTest):
    snippets = (
        ("m", r"_${0:explicit zero}", "snip", "i"),
    )
    keys = "m" + EX + "hello m" + EX + "world m" + EX + "end"
    wanted = r"_hello _world _end"
class RecTabsStops_BackspaceZero_ECR(_VimTest):
    snippets = (
        ("m", r"${1:one}${0:explicit zero}${2:two}", "snip", "i"),
    )
    keys = "m" + EX + JF + JF + BS + "m" + EX
    wanted = r"oneoneexplicit zerotwotwo"


class RecTabStops_MirrorInnerSnippet_ECR(_VimTest):
    snippets = (
        ("m", "[ $1 $2 ] $1"),
        ("m1", "ASnip $1 ASnip $2 ASnip"),
    )
    keys = "m" + EX + "m1" + EX + "Hallo" + JF + "Hi" + JF + "endone" + JF + "two" + JF + "totalend"
    wanted = "[ ASnip Hallo ASnip Hi ASnipendone two ] ASnip Hallo ASnip Hi ASnipendonetotalend"

class RecTabStops_NotAtBeginningOfTS_ExpectCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "hello m" + EX + "hi" + JF + "two" + JF + "ups" + JF + "three" + \
            JF + "end"
    wanted = "[ hello [ hi  two ]ups  three ]end"
class RecTabStops_InNewlineInTabstop_ExpectCorrectResult(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "hello\nm" + EX + "hi" + JF + "two" + JF + "ups" + JF + "three" + \
            JF + "end"
    wanted = "[ hello\n[ hi  two ]ups  three ]end"
class RecTabStops_InNewlineInTabstopNotAtBeginOfLine_ECR(_VimTest):
    snippets = ("m", "[ ${1:first}  ${2:sec} ]")
    keys = "m" + EX + "hello\nhello again m" + EX + "hi" + JF + "two" + \
            JF + "ups" + JF + "three" + JF + "end"
    wanted = "[ hello\nhello again [ hi  two ]ups  three ]end"

class RecTabStops_InNewlineMultiline_ECR(_VimTest):
    snippets = ("m", "M START\n$0\nM END")
    keys = "m" + EX + "m" + EX
    wanted = "M START\nM START\n\nM END\nM END"
class RecTabStops_InNewlineManualIndent_ECR(_VimTest):
    snippets = ("m", "M START\n$0\nM END")
    keys = "m" + EX + "    m" + EX + "hi"
    wanted = "M START\n    M START\n    hi\n    M END\nM END"
class RecTabStops_InNewlineManualIndentTextInFront_ECR(_VimTest):
    snippets = ("m", "M START\n$0\nM END")
    keys = "m" + EX + "    hallo m" + EX + "hi"
    wanted = "M START\n    hallo M START\n    hi\n    M END\nM END"
class RecTabStops_InNewlineMultilineWithIndent_ECR(_VimTest):
    snippets = ("m", "M START\n    $0\nM END")
    keys = "m" + EX + "m" + EX + "hi"
    wanted = "M START\n    M START\n        hi\n    M END\nM END"
class RecTabStops_InNewlineMultilineWithNonZeroTS_ECR(_VimTest):
    snippets = ("m", "M START\n    $1\nM END -> $0")
    keys = "m" + EX + "m" + EX + "hi" + JF + "hallo" + JF + "end"
    wanted = "M START\n    M START\n        hi\n    M END -> hallo\n" \
        "M END -> end"

class RecTabStops_BarelyNotLeavingInner_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "a" + 3*ARR_L + JF + "hallo" + \
            JF + "ups" + JF + "world" + JF + "end"
    wanted = "[ [ a hallo ]ups world ]end"
class RecTabStops_LeavingInner_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "a" + 4*ARR_L + JF + "hallo" + \
            JF + "world"
    wanted = "[ [ a sec ] hallo ]world"
class RecTabStops_LeavingInnerInner_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "m" + EX + "a" + 4*ARR_L + JF + "hallo" + \
            JF + "ups" + JF + "world" + JF + "end"
    wanted = "[ [ [ a sec ] hallo ]ups world ]end"
class RecTabStops_LeavingInnerInnerTwo_ECR(_VimTest):
    snippets = (
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m" + EX + "m" + EX + "a" + 6*ARR_L + JF + "hallo" + \
            JF + "end"
    wanted = "[ [ [ a sec ] sec ] hallo ]end"


class RecTabStops_ZeroTSisNothingSpecial_ECR(_VimTest):
    snippets = (
        ("m1", "[ ${1:first} $0 ${2:sec} ]"),
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + "one" + JF + "two" + \
            JF + "three" + JF + "four" + JF + "end"
    wanted = "[ [ one three two ] four ]end"
class RecTabStops_MirroredZeroTS_ECR(_VimTest):
    snippets = (
        ("m1", "[ ${1:first} ${0:Year, some default text} $0 ${2:sec} ]"),
        ("m", "[ ${1:first} ${2:sec} ]"),
    )
    keys = "m" + EX + "m1" + EX + "one" + JF + "two" + \
            JF + "three" + JF + "four" + JF + "end"
    wanted = "[ [ one three three two ] four ]end"
class RecTabStops_ChildTriggerContainsParentTextObjects(_VimTest):
    # https://bugs.launchpad.net/bugs/1191617
    files = { "us/all.snippets": r"""
global !p
def complete(t, opts):
 if t:
   opts = [ q[len(t):] for q in opts if q.startswith(t) ]
 if len(opts) == 0:
   return ''
 return opts[0] if len(opts) == 1 else "(" + '|'.join(opts) + ')'
def autocomplete_options(t, string, attr=None):
   return complete(t[1], [opt for opt in attr if opt not in string])
endglobal
snippet /form_for(.*){([^|]*)/ "form_for html options" rw!
`!p
auto = autocomplete_options(t, match.group(2), attr=["id: ", "class: ", "title:  "])
snip.rv = "form_for" + match.group(1) + "{"`$1`!p if (snip.c != auto) : snip.rv=auto`
endsnippet
"""}
    keys = "form_for user, namespace: some_namespace, html: {i" + EX + "i" + EX
    wanted = "form_for user, namespace: some_namespace, html: {(id: |class: |title:  )d: "
# End: Recursive (Nested) Snippets  #}}}
# List Snippets  {{{#
class _ListAllSnippets(_VimTest):
    snippets = ( ("testblah", "BLAAH", "Say BLAH"),
                 ("test", "TEST ONE", "Say tst one"),
                 ("aloha", "OHEEEE",   "Say OHEE"),
               )

class ListAllAvailable_NothingTyped_ExpectCorrectResult(_ListAllSnippets):
    keys = "" + LS + "3\n"
    wanted = "BLAAH"
class ListAllAvailable_SpaceInFront_ExpectCorrectResult(_ListAllSnippets):
    keys = " " + LS + "3\n"
    wanted = " BLAAH"
class ListAllAvailable_BraceInFront_ExpectCorrectResult(_ListAllSnippets):
    keys = "} " + LS + "3\n"
    wanted = "} BLAAH"
class ListAllAvailable_testtyped_ExpectCorrectResult(_ListAllSnippets):
    keys = "hallo test" + LS + "2\n"
    wanted = "hallo BLAAH"
class ListAllAvailable_testtypedSecondOpt_ExpectCorrectResult(_ListAllSnippets):
    keys = "hallo test" + LS + "1\n"
    wanted = "hallo TEST ONE"

class ListAllAvailable_NonDefined_NoExpectionShouldBeRaised(_ListAllSnippets):
    keys = "hallo qualle" + LS + "Hi"
    wanted = "hallo qualleHi"
# End: List Snippets  #}}}
# Selecting Between Same Triggers  {{{#
class _MultipleMatches(_VimTest):
    snippets = ( ("test", "Case1", "This is Case 1"),
                 ("test", "Case2", "This is Case 2") )
class Multiple_SimpleCaseSelectFirst_ECR(_MultipleMatches):
    keys = "test" + EX + "1\n"
    wanted = "Case1"
class Multiple_SimpleCaseSelectSecond_ECR(_MultipleMatches):
    keys = "test" + EX + "2\n"
    wanted = "Case2"
class Multiple_SimpleCaseSelectTooHigh_ESelectLast(_MultipleMatches):
    keys = "test" + EX + "5\n"
    wanted = "Case2"
class Multiple_SimpleCaseSelectZero_EEscape(_MultipleMatches):
    keys = "test" + EX + "0\n" + "hi"
    wanted = "testhi"
class Multiple_SimpleCaseEscapeOut_ECR(_MultipleMatches):
    keys = "test" + EX + ESC + "hi"
    wanted = "testhi"
class Multiple_ManySnippetsOneTrigger_ECR(_VimTest):
    # Snippet definition {{{#
    snippets = (
        ("test", "Case1", "This is Case 1"),
        ("test", "Case2", "This is Case 2"),
        ("test", "Case3", "This is Case 3"),
        ("test", "Case4", "This is Case 4"),
        ("test", "Case5", "This is Case 5"),
        ("test", "Case6", "This is Case 6"),
        ("test", "Case7", "This is Case 7"),
        ("test", "Case8", "This is Case 8"),
        ("test", "Case9", "This is Case 9"),
        ("test", "Case10", "This is Case 10"),
        ("test", "Case11", "This is Case 11"),
        ("test", "Case12", "This is Case 12"),
        ("test", "Case13", "This is Case 13"),
        ("test", "Case14", "This is Case 14"),
        ("test", "Case15", "This is Case 15"),
        ("test", "Case16", "This is Case 16"),
        ("test", "Case17", "This is Case 17"),
        ("test", "Case18", "This is Case 18"),
        ("test", "Case19", "This is Case 19"),
        ("test", "Case20", "This is Case 20"),
        ("test", "Case21", "This is Case 21"),
        ("test", "Case22", "This is Case 22"),
        ("test", "Case23", "This is Case 23"),
        ("test", "Case24", "This is Case 24"),
        ("test", "Case25", "This is Case 25"),
        ("test", "Case26", "This is Case 26"),
        ("test", "Case27", "This is Case 27"),
        ("test", "Case28", "This is Case 28"),
        ("test", "Case29", "This is Case 29"),
    ) #}}}
    keys = "test" + EX + " " + ESC + ESC + "ahi"
    wanted = "testhi"
# End: Selecting Between Same Triggers  #}}}
# Snippet Priority  {{{#
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
    files = { "us/all.snippets": r"""
        snippet test "Test Snippet" b
        This is a test snippet
        endsnippet
        """}
    snippets = (
        ("test", "We overwrite", "Overwrite the two", "", 1),
    )
    keys = "test" + EX
    wanted = "We overwrite"
class SnippetPriorities_FileHasHigherThanAdded(_VimTest):
    files = { "us/all.snippets": r"""
        snippet test "Test Snippet" b
        This is a test snippet
        endsnippet
        """}
    snippets = (
        ("test", "We do not overwrite", "Overwrite the two", "", -1),
    )
    keys = "test" + EX
    wanted = "This is a test snippet"
class SnippetPriorities_FileHasHigherThanAdded(_VimTest):
    files = { "us/all.snippets": r"""
        priority -3
        snippet test "Test Snippet" b
        This is a test snippet
        endsnippet
        """}
    snippets = (
        ("test", "We overwrite", "Overwrite the two", "", -5),
    )
    keys = "test" + EX
    wanted = "This is a test snippet"
# End: Snippet Priority  #}}}


# Snippet Options  {{{#
class SnippetOptions_OnlyExpandWhenWSInFront_Expand(_VimTest):
    snippets = ("test", "Expand me!", "", "b")
    keys = "test" + EX
    wanted = "Expand me!"
class SnippetOptions_OnlyExpandWhenWSInFront_Expand2(_VimTest):
    snippets = ("test", "Expand me!", "", "b")
    keys = "   test" + EX
    wanted = "   Expand me!"
class SnippetOptions_OnlyExpandWhenWSInFront_DontExpand(_VimTest):
    snippets = ("test", "Expand me!", "", "b")
    keys = "a test" + EX
    wanted = "a test" + EX
class SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWO(_VimTest):
    snippets = (
        ("test", "Expand me!", "", "b"),
        ("test", "not at beginning", "", ""),
    )
    keys = "a test" + EX
    wanted = "a not at beginning"
class SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWOChoose(_VimTest):
    snippets = (
        ("test", "Expand me!", "", "b"),
        ("test", "not at beginning", "", ""),
    )
    keys = "  test" + EX + "1\n"
    wanted = "  Expand me!"


class SnippetOptions_ExpandInwordSnippets_SimpleExpand(_VimTest):
    snippets = (("test", "Expand me!", "", "i"), )
    keys = "atest" + EX
    wanted = "aExpand me!"
class SnippetOptions_ExpandInwordSnippets_ExpandSingle(_VimTest):
    snippets = (("test", "Expand me!", "", "i"), )
    keys = "test" + EX
    wanted = "Expand me!"
class SnippetOptions_ExpandInwordSnippetsWithOtherChars_Expand(_VimTest):
    snippets = (("test", "Expand me!", "", "i"), )
    keys = "$test" + EX
    wanted = "$Expand me!"
class SnippetOptions_ExpandInwordSnippetsWithOtherChars_Expand2(_VimTest):
    snippets = (("test", "Expand me!", "", "i"), )
    keys = "-test" + EX
    wanted = "-Expand me!"
class SnippetOptions_ExpandInwordSnippetsWithOtherChars_Expand3(_VimTest):
    skip_if = lambda self: running_on_windows()
    snippets = (("test", "Expand me!", "", "i"), )
    keys = "ßßtest" + EX
    wanted = "ßßExpand me!"

class _SnippetOptions_ExpandWordSnippets(_VimTest):
    snippets = (("test", "Expand me!", "", "w"), )
class SnippetOptions_ExpandWordSnippets_NormalExpand(
        _SnippetOptions_ExpandWordSnippets):
    keys = "test" + EX
    wanted = "Expand me!"
class SnippetOptions_ExpandWordSnippets_NoExpand(
    _SnippetOptions_ExpandWordSnippets):
    keys = "atest" + EX
    wanted = "atest" + EX
class SnippetOptions_ExpandWordSnippets_ExpandSuffix(
    _SnippetOptions_ExpandWordSnippets):
    keys = "a-test" + EX
    wanted = "a-Expand me!"
class SnippetOptions_ExpandWordSnippets_ExpandSuffix2(
    _SnippetOptions_ExpandWordSnippets):
    keys = "a(test" + EX
    wanted = "a(Expand me!"
class SnippetOptions_ExpandWordSnippets_ExpandSuffix3(
    _SnippetOptions_ExpandWordSnippets):
    keys = "[[test" + EX
    wanted = "[[Expand me!"

class _No_Tab_Expand(_VimTest):
    snippets = ("test", "\t\tExpand\tme!\t", "", "t")
class No_Tab_Expand_Simple(_No_Tab_Expand):
    keys = "test" + EX
    wanted = "\t\tExpand\tme!\t"
class No_Tab_Expand_Leading_Spaces(_No_Tab_Expand):
    keys = "  test" + EX
    wanted = "  \t\tExpand\tme!\t"
class No_Tab_Expand_Leading_Tabs(_No_Tab_Expand):
    keys = "\ttest" + EX
    wanted = "\t\t\tExpand\tme!\t"
class No_Tab_Expand_No_TS(_No_Tab_Expand):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set sts=3")
    keys = "test" + EX
    wanted = "\t\tExpand\tme!\t"
class No_Tab_Expand_ET(_No_Tab_Expand):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set expandtab")
    keys = "test" + EX
    wanted = "\t\tExpand\tme!\t"
class No_Tab_Expand_ET_Leading_Spaces(_No_Tab_Expand):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set expandtab")
    keys = "  test" + EX
    wanted = "  \t\tExpand\tme!\t"
class No_Tab_Expand_ET_SW(_No_Tab_Expand):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=8")
        vim_config.append("set expandtab")
    keys = "test" + EX
    wanted = "\t\tExpand\tme!\t"
class No_Tab_Expand_ET_SW_TS(_No_Tab_Expand):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set sts=3")
        vim_config.append("set ts=3")
        vim_config.append("set expandtab")
    keys = "test" + EX
    wanted = "\t\tExpand\tme!\t"

class _TabExpand_RealWorld(object):
    snippets = ("hi",
r"""hi
`!p snip.rv="i1\n"
snip.rv += snip.mkline("i1\n")
snip.shift(1)
snip.rv += snip.mkline("i2\n")
snip.unshift(2)
snip.rv += snip.mkline("i0\n")
snip.shift(3)
snip.rv += snip.mkline("i3")`
snip.rv = repr(snip.rv)
End""")

class No_Tab_Expand_RealWorld(_TabExpand_RealWorld,_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set noexpandtab")
    keys = "\t\thi" + EX
    wanted = """\t\thi
\t\ti1
\t\ti1
\t\t\ti2
\ti0
\t\t\t\ti3
\t\tsnip.rv = repr(snip.rv)
\t\tEnd"""


class SnippetOptions_Regex_Expand(_VimTest):
    snippets = ("(test)", "Expand me!", "", "r")
    keys = "test" + EX
    wanted = "Expand me!"
class SnippetOptions_Regex_Multiple(_VimTest):
    snippets = ("(test *)+", "Expand me!", "", "r")
    keys = "test test test" + EX
    wanted = "Expand me!"

class _Regex_Self(_VimTest):
    snippets = ("((?<=\W)|^)(\.)", "self.", "", "r")
class SnippetOptions_Regex_Self_Start(_Regex_Self):
    keys = "." + EX
    wanted = "self."
class SnippetOptions_Regex_Self_Space(_Regex_Self):
    keys = " ." + EX
    wanted = " self."
class SnippetOptions_Regex_Self_TextAfter(_Regex_Self):
    keys = " .a" + EX
    wanted = " .a" + EX
class SnippetOptions_Regex_Self_TextBefore(_Regex_Self):
    keys = "a." + EX
    wanted = "a." + EX
class SnippetOptions_Regex_PythonBlockMatch(_VimTest):
    snippets = (r"([abc]+)([def]+)", r"""`!p m = match
snip.rv += m.group(2)
snip.rv += m.group(1)
`""", "", "r")
    keys = "test cabfed" + EX
    wanted = "test fedcab"
class SnippetOptions_Regex_PythonBlockNoMatch(_VimTest):
    snippets = (r"cabfed", r"""`!p snip.rv =  match or "No match"`""")
    keys = "test cabfed" + EX
    wanted = "test No match"
# Tests for Bug #691575
class SnippetOptions_Regex_SameLine_Long_End(_VimTest):
    snippets = ("(test.*)", "Expand me!", "", "r")
    keys = "test test abc" + EX
    wanted = "Expand me!"
class SnippetOptions_Regex_SameLine_Long_Start(_VimTest):
    snippets = ("(.*test)", "Expand me!", "", "r")
    keys = "abc test test" + EX
    wanted = "Expand me!"
class SnippetOptions_Regex_SameLine_Simple(_VimTest):
    snippets = ("(test)", "Expand me!", "", "r")
    keys = "abc test test" + EX
    wanted = "abc test Expand me!"


class MultiWordSnippet_Simple(_VimTest):
    snippets = ("test me", "Expand me!")
    keys = "test me" + EX
    wanted = "Expand me!"
class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_Expand(_VimTest):
    snippets = ("test it", "Expand me!", "", "b")
    keys = "test it" + EX
    wanted = "Expand me!"
class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_Expand2(_VimTest):
    snippets = ("test it", "Expand me!", "", "b")
    keys = "   test it" + EX
    wanted = "   Expand me!"
class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_DontExpand(_VimTest):
    snippets = ("test it", "Expand me!", "", "b")
    keys = "a test it" + EX
    wanted = "a test it" + EX
class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWO(_VimTest):
    snippets = (
        ("test it", "Expand me!", "", "b"),
        ("test it", "not at beginning", "", ""),
    )
    keys = "a test it" + EX
    wanted = "a not at beginning"
class MultiWord_SnippetOptions_OnlyExpandWhenWSInFront_OneWithOneWOChoose(_VimTest):
    snippets = (
        ("test it", "Expand me!", "", "b"),
        ("test it", "not at beginning", "", ""),
    )
    keys = "  test it" + EX + "1\n"
    wanted = "  Expand me!"

class MultiWord_SnippetOptions_ExpandInwordSnippets_SimpleExpand(_VimTest):
    snippets = (("test it", "Expand me!", "", "i"), )
    keys = "atest it" + EX
    wanted = "aExpand me!"
class MultiWord_SnippetOptions_ExpandInwordSnippets_ExpandSingle(_VimTest):
    snippets = (("test it", "Expand me!", "", "i"), )
    keys = "test it" + EX
    wanted = "Expand me!"

class _MultiWord_SnippetOptions_ExpandWordSnippets(_VimTest):
    snippets = (("test it", "Expand me!", "", "w"), )
class MultiWord_SnippetOptions_ExpandWordSnippets_NormalExpand(
        _MultiWord_SnippetOptions_ExpandWordSnippets):
    keys = "test it" + EX
    wanted = "Expand me!"
class MultiWord_SnippetOptions_ExpandWordSnippets_NoExpand(
    _MultiWord_SnippetOptions_ExpandWordSnippets):
    keys = "atest it" + EX
    wanted = "atest it" + EX
class MultiWord_SnippetOptions_ExpandWordSnippets_ExpandSuffix(
    _MultiWord_SnippetOptions_ExpandWordSnippets):
    keys = "a-test it" + EX
    wanted = "a-Expand me!"
# Snippet Options  #}}}

# Anonymous Expansion  {{{#
class _AnonBase(_VimTest):
    args = ""
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("inoremap <silent> %s <C-R>=UltiSnips#Anon(%s)<cr>"
                % (EA, self.args))

class Anon_NoTrigger_Simple(_AnonBase):
    args = '"simple expand"'
    keys = "abc" + EA
    wanted = "abcsimple expand"

class Anon_NoTrigger_AfterSpace(_AnonBase):
    args = '"simple expand"'
    keys = "abc " + EA
    wanted = "abc simple expand"

class Anon_NoTrigger_BeginningOfLine(_AnonBase):
    args = r"':latex:\`$1\`$0'"
    keys = EA + "Hello" + JF + "World"
    wanted = ":latex:`Hello`World"
class Anon_NoTrigger_FirstCharOfLine(_AnonBase):
    args = r"':latex:\`$1\`$0'"
    keys = " " + EA + "Hello" + JF + "World"
    wanted = " :latex:`Hello`World"

class Anon_NoTrigger_Multi(_AnonBase):
    args = '"simple $1 expand $1 $0"'
    keys = "abc" + EA + "123" + JF + "456"
    wanted = "abcsimple 123 expand 123 456"

class Anon_Trigger_Multi(_AnonBase):
    args = '"simple $1 expand $1 $0", "abc"'
    keys = "123 abc" + EA + "123" + JF + "456"
    wanted = "123 simple 123 expand 123 456"

class Anon_Trigger_Simple(_AnonBase):
    args = '"simple expand", "abc"'
    keys = "abc" + EA
    wanted = "simple expand"

class Anon_Trigger_Twice(_AnonBase):
    args = '"simple expand", "abc"'
    keys = "abc" + EA + "\nabc" + EX
    wanted = "simple expand\nabc" + EX

class Anon_Trigger_Opts(_AnonBase):
    args = '"simple expand", ".*abc", "desc", "r"'
    keys = "blah blah abc" + EA
    wanted = "simple expand"
# End: Anonymous Expansion  #}}}
# AddSnippet Function  {{{#
class _AddFuncBase(_VimTest):
    args = ""
    def _extra_options_pre_init(self, vim_config):
        vim_config.append(":call UltiSnips#AddSnippetWithPriority(%s)" %
                self.args)

class AddFunc_Simple(_AddFuncBase):
    args = '"test", "simple expand", "desc", "", "all", 0'
    keys = "abc test" + EX
    wanted = "abc simple expand"

class AddFunc_Opt(_AddFuncBase):
    args = '".*test", "simple expand", "desc", "r", "all", 0'
    keys = "abc test" + EX
    wanted = "simple expand"
# End: AddSnippet Function  #}}}

# ExpandTab  {{{#
class _ExpandTabs(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set sw=3")
        vim_config.append("set expandtab")

class RecTabStopsWithExpandtab_SimpleExample_ECR(_ExpandTabs):
    snippets = ("m", "\tBlaahblah \t\t  ")
    keys = "m" + EX
    wanted = "   Blaahblah \t\t  "

class RecTabStopsWithExpandtab_SpecialIndentProblem_ECR(_ExpandTabs):
    # Windows indents the Something line after pressing return, though it
    # shouldn't because it contains a manual indent. All other vim versions do
    # not do this. Windows vim does not interpret the changes made by :py as
    # changes made 'manually', while the other vim version seem to do so. Since
    # the fault is not with UltiSnips, we simply skip this test on windows
    # completely.
    skip_if = lambda self: running_on_windows()
    snippets = (
        ("m1", "Something"),
        ("m", "\t$0"),
    )
    keys = "m" + EX + "m1" + EX + '\nHallo'
    wanted = "   Something\n        Hallo"
    def _extra_options_pre_init(self, vim_config):
        _ExpandTabs._extra_options_pre_init(self, vim_config)
        vim_config.append("set indentkeys=o,O,*<Return>,<>>,{,}")
        vim_config.append("set indentexpr=8")
# End: ExpandTab  #}}}
# Proper Indenting  {{{#
class ProperIndenting_SimpleCase_ECR(_VimTest):
    snippets = ("test", "for\n    blah")
    keys = "    test" + EX + "Hui"
    wanted = "    for\n        blahHui"
class ProperIndenting_SingleLineNoReindenting_ECR(_VimTest):
    snippets = ("test", "hui")
    keys = "    test" + EX + "blah"
    wanted = "    huiblah"
class ProperIndenting_AutoIndentAndNewline_ECR(_VimTest):
    snippets = ("test", "hui")
    keys = "    test" + EX + "\n"+ "blah"
    wanted = "    hui\n    blah"
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set autoindent")
# Test for bug 1073816
class ProperIndenting_FirstLineInFile_ECR(_VimTest):
    text_before = ""
    text_after = ""
    files = { "us/all.snippets": r"""
global !p
def complete(t, opts):
  if t:
    opts = [ m[len(t):] for m in opts if m.startswith(t) ]
  if len(opts) == 1:
    return opts[0]
  elif len(opts) > 1:
    return "(" + "|".join(opts) + ")"
  else:
    return ""
endglobal

snippet '^#?inc' "#include <>" !r
#include <$1`!p snip.rv = complete(t[1], ['cassert', 'cstdio', 'cstdlib', 'cstring', 'fstream', 'iostream', 'sstream'])`>
endsnippet
        """}
    keys = "inc" + EX + "foo"
    wanted = "#include <foo>"
class ProperIndenting_FirstLineInFileComplete_ECR(ProperIndenting_FirstLineInFile_ECR):
    keys = "inc" + EX + "cstdl"
    wanted = "#include <cstdlib>"
# End: Proper Indenting  #}}}
# Format options tests  {{{#
class _FormatoptionsBase(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set tw=20")
        vim_config.append("set fo=lrqntc")

class FOSimple_Break_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ("test", "${1:longer expand}\n$1\n$0", "", "f")
    keys = "test" + EX + "This is a longer text that should wrap as formatoptions are  enabled" + JF + "end"
    wanted = "This is a longer\ntext that should\nwrap as\nformatoptions are\nenabled\n" + \
        "This is a longer\ntext that should\nwrap as\nformatoptions are\nenabled\n" + "end"


class FOTextBeforeAndAfter_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ("test", "Before${1:longer expand}After\nstart$1end")
    keys = "test" + EX + "This is a longer text that should wrap"
    wanted = \
"""BeforeThis is a
longer text that
should wrapAfter
startThis is a
longer text that
should wrapend"""


# Tests for https://bugs.launchpad.net/bugs/719998
class FOTextAfter_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ("test", "${1:longer expand}after\nstart$1end")
    keys = ("test" + EX + "This is a longer snippet that should wrap properly "
            "and the mirror below should work as well")
    wanted = \
"""This is a longer
snippet that should
wrap properly and
the mirror below
should work as wellafter
startThis is a longer
snippet that should
wrap properly and
the mirror below
should work as wellend"""

class FOWrapOnLongWord_ExpectCorrectResult(_FormatoptionsBase):
    snippets = ("test", "${1:longer expand}after\nstart$1end")
    keys = ("test" + EX + "This is a longersnippet that should wrap properly")
    wanted = \
"""This is a
longersnippet that
should wrap properlyafter
startThis is a
longersnippet that
should wrap properlyend"""
# End: Format options tests  #}}}
# Langmap Handling  {{{#
# Test for bug 501727 #
class TestNonEmptyLangmap_ExpectCorrectResult(_VimTest):
    snippets = ("testme",
"""my snipped ${1:some_default}
and a mirror: $1
$2...$3
$0""")
    keys = "testme" + EX + "hi1" + JF + "hi2" + JF + "hi3" + JF + "hi4"
    wanted ="""my snipped hi1
and a mirror: hi1
hi2...hi3
hi4"""
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set langmap=dj,rk,nl,ln,jd,kr,DJ,RK,NL,LN,JD,KR")

# Test for https://bugs.launchpad.net/bugs/501727 #
class TestNonEmptyLangmapWithSemi_ExpectCorrectResult(_VimTest):
    snippets = ("testme",
"""my snipped ${1:some_default}
and a mirror: $1
$2...$3
$0""")
    keys = "testme" + EX + "hi;" + JF + "hi2" + JF + "hi3" + JF + "hi4" + ESC + ";Hello"
    wanted ="""my snipped hi;
and a mirror: hi;
hi2...hi3
hi4Hello"""

    def _before_test(self):
        self.vim.send(":set langmap=\\\\;;A\n")

# Test for bug 871357 #
class TestLangmapWithUtf8_ExpectCorrectResult(_VimTest):
    skip_if = lambda self: running_on_windows()  # SendKeys can't send UTF characters
    snippets = ("testme",
"""my snipped ${1:some_default}
and a mirror: $1
$2...$3
$0""")
    keys = "testme" + EX + "hi1" + JF + "hi2" + JF + "hi3" + JF + "hi4"
    wanted ="""my snipped hi1
and a mirror: hi1
hi2...hi3
hi4"""

    def _before_test(self):
        self.vim.send(":set langmap=йq,цw,уe,кr,еt,нy,гu,шi,щo,зp,х[,ъ],фa,ыs,вd,аf,пg,рh,оj,лk,дl,ж\\;,э',яz,чx,сc,мv,иb,тn,ьm,ю.,ё',ЙQ,ЦW,УE,КR,ЕT,НY,ГU,ШI,ЩO,ЗP,Х\{,Ъ\},ФA,ЫS,ВD,АF,ПG,РH,ОJ,ЛK,ДL,Ж\:,Э\",ЯZ,ЧX,СC,МV,ИB,ТN,ЬM,Б\<,Ю\>\n")

# End: Langmap Handling  #}}}
# Unmap SelectMode Mappings  {{{#
# Test for bug 427298 #
class _SelectModeMappings(_VimTest):
    snippets = ("test", "${1:World}")
    keys = "test" + EX + "Hello"
    wanted = "Hello"
    maps = ("", "")
    buffer_maps = ("", "")
    do_unmapping = True
    ignores = []

    def _extra_options_pre_init(self, vim_config):
        vim_config.append(":let g:UltiSnipsRemoveSelectModeMappings=%i" % int(self.do_unmapping))
        vim_config.append(":let g:UltiSnipsMappingsToIgnore=%s" % repr(self.ignores))

        if not isinstance(self.maps[0], tuple):
            self.maps = (self.maps,)
        if not isinstance(self.buffer_maps[0], tuple):
            self.buffer_maps = (self.buffer_maps,)

        for key, m in self.maps:
            if not len(key): continue
            vim_config.append(":smap %s %s" % (key,m))
        for key, m in self.buffer_maps:
            if not len(key): continue
            vim_config.append(":smap <buffer> %s %s" % (key,m))

class SelectModeMappings_RemoveBeforeSelecting_ECR(_SelectModeMappings):
    maps = ("H", "x")
    wanted = "Hello"
class SelectModeMappings_DisableRemoveBeforeSelecting_ECR(_SelectModeMappings):
    do_unmapping = False
    maps = ("H", "x")
    wanted = "xello"
class SelectModeMappings_IgnoreMappings_ECR(_SelectModeMappings):
    ignores = ["e"]
    maps = ("H", "x"), ("e", "l")
    wanted = "Hello"
class SelectModeMappings_IgnoreMappings1_ECR(_SelectModeMappings):
    ignores = ["H"]
    maps = ("H", "x"), ("e", "l")
    wanted = "xello"
class SelectModeMappings_IgnoreMappings2_ECR(_SelectModeMappings):
    ignores = ["e", "H"]
    maps = ("e", "l"), ("H", "x")
    wanted = "xello"
class SelectModeMappings_BufferLocalMappings_ECR(_SelectModeMappings):
    buffer_maps = ("H", "blah")
    wanted = "Hello"

# End: Unmap SelectMode Mappings  #}}}
# Folding Interaction  {{{#
class FoldingEnabled_SnippetWithFold_ExpectNoFolding(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set foldlevel=0")
        vim_config.append("set foldmethod=marker")
    snippets = ("test", r"""Hello {{{
${1:Welt} }}}""")
    keys = "test" + EX + "Ball"
    wanted = """Hello {{{
Ball }}}"""
class FoldOverwrite_Simple_ECR(_VimTest):
    snippets = ("fold",
"""# ${1:Description}  `!p snip.rv = vim.eval("&foldmarker").split(",")[0]`

# End: $1  `!p snip.rv = vim.eval("&foldmarker").split(",")[1]`""")
    keys = "fold" + EX + "hi"
    wanted = "# hi  {{{\n\n# End: hi  }}}"
class Fold_DeleteMiddleLine_ECR(_VimTest):
    snippets = ("fold",
"""# ${1:Description}  `!p snip.rv = vim.eval("&foldmarker").split(",")[0]`


# End: $1  `!p snip.rv = vim.eval("&foldmarker").split(",")[1]`""")
    keys = "fold" + EX + "hi" + ESC + "jdd"
    wanted = "# hi  {{{\n\n# End: hi  }}}"

class PerlSyntaxFold(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set foldlevel=0")
        vim_config.append("syntax enable")
        vim_config.append("set foldmethod=syntax")
        vim_config.append("let g:perl_fold = 1")
        vim_config.append("so $VIMRUNTIME/syntax/perl.vim")
    snippets = ("test", r"""package ${1:`!v printf('c%02d', 3)`};
${0}
1;""")
    keys = "test" + EX + JF + "sub junk {}"
    wanted = "package c03;\nsub junk {}\n1;"
# End: Folding Interaction  #}}}
# Trailing whitespace {{{#
class RemoveTrailingWhitespace(_VimTest):
    snippets = ("test", """Hello\t ${1:default}\n$2""", "", "s")
    wanted = """Hello\nGoodbye"""
    keys = "test" + EX + BS + JF + "Goodbye"
class LeaveTrailingWhitespace(_VimTest):
    snippets = ("test", """Hello \t ${1:default}\n$2""")
    wanted = """Hello \t \nGoodbye"""
    keys = "test" + EX + BS + JF + "Goodbye"
# End: Trailing whitespace #}}}

# Cursor Movement  {{{#
class CursorMovement_Multiline_ECR(_VimTest):
    snippets = ("test", r"$1 ${1:a tab}")
    keys = "test" + EX + "this is something\nvery nice\nnot" + JF + "more text"
    wanted = "this is something\nvery nice\nnot " \
            "this is something\nvery nice\nnotmore text"
class CursorMovement_BS_InEditMode(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set backspace=eol,indent,start")
    snippets = ("<trh", "<tr>\n\t<th>$1</th>\n\t$2\n</tr>\n$3")
    keys = "<trh" + EX + "blah" + JF + BS + BS + JF + "end"
    wanted = "<tr>\n\t<th>blah</th>\n</tr>\nend"
# End: Cursor Movement  #}}}
# Insert Mode Moving  {{{#
class IMMoving_CursorsKeys_ECR(_VimTest):
    snippets = ("test", "${1:Some}")
    keys = "test" + EX + "text" + 3*ARR_U + 6*ARR_D
    wanted = "text"
class IMMoving_AcceptInputWhenMoved_ECR(_VimTest):
    snippets = ("test", r"$1 ${1:a tab}")
    keys = "test" + EX + "this" + 2*ARR_L + "hallo\nwelt"
    wanted = "thhallo\nweltis thhallo\nweltis"
class IMMoving_NoExiting_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:a tab} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 7*ARR_L + \
            JF + "hallo"
    wanted = "hello tab hallo tab this"
class IMMoving_NoExitingEventAtEnd_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:a tab} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + JF + "hallo"
    wanted = "hello tab hallo tab this"
class IMMoving_ExitWhenOutsideRight_ECR(_VimTest):
    snippets = ("test", r"$1 ${2:blub} ${1:Tab}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + ARR_R + JF + "hallo"
    wanted = "hello tab blub tab " + JF + "hallothis"
class IMMoving_NotExitingWhenBarelyOutsideLeft_ECR(_VimTest):
    snippets = ("test", r"${1:Hi} ${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 3*ARR_L + \
            JF + "hallo"
    wanted = "hello tab hallo this"
class IMMoving_ExitWhenOutsideLeft_ECR(_VimTest):
    snippets = ("test", r"${1:Hi} ${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 4*ARR_L + \
            JF + "hallo"
    wanted = "hello" + JF + "hallo tab blub this"
class IMMoving_ExitWhenOutsideAbove_ECR(_VimTest):
    snippets = ("test", "${1:Hi}\n${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 1*ARR_U + "\n" + JF + \
            "hallo"
    wanted = JF + "hallo\nhello tab\nblub this"
class IMMoving_ExitWhenOutsideBelow_ECR(_VimTest):
    snippets = ("test", "${1:Hi}\n${2:blub}")
    keys = "hello test this" + ESC + "02f i" + EX + "tab" + 2*ARR_D + JF + \
            "testhallo\n"
    wanted = "hello tab\nblub this\n" + JF + "testhallo"
# End: Insert Mode Moving  #}}}
# Undo of Snippet insertion  {{{#
class Undo_RemoveMultilineSnippet(_VimTest):
    snippets = ("test", "Hello\naaa ${1} bbb\nWorld")
    keys = "test" + EX + ESC + "u" + "inothing"
    wanted = "nothing"
class Undo_RemoveEditInTabstop(_VimTest):
    snippets = ("test", "$1 Hello\naaa ${1} bbb\nWorld")
    keys = "hello test" + EX + "upsi" + ESC + "hh" + "iabcdef" + ESC + "u"
    wanted = "hello upsi Hello\naaa upsi bbb\nWorld"
class Undo_RemoveWholeSnippet(_VimTest):
    snippets = ("test", "Hello\n${1:Hello}World")
    keys = "first line\n\n\n\n\n\nthird line" + \
            ESC + "3k0itest" + EX + ESC + "uiupsy"
    wanted = "first line\n\n\nupsy\n\n\nthird line"
class JumpForward_DefSnippet(_VimTest):
    snippets = ("test", "${1}\n`!p snip.rv = '\\n'.join(t[1].split())`\n\n${0:pass}")
    keys = "test" + EX + "a b c" + JF + "shallnot"
    wanted = "a b c\na\nb\nc\n\nshallnot"
class DeleteSnippetInsertion0(_VimTest):
    snippets = ("test", "${1:hello} $1")
    keys = "test" + EX + ESC + "Vkx" + "i\nworld\n"
    wanted = "world"
class DeleteSnippetInsertion1(_VimTest):
    snippets = ("test", r"$1${1/(.*)/(?0::.)/}")
    keys = "test" + EX + ESC + "u" + "i" + JF + "\t"
    wanted = "\t"
# End: Undo of Snippet insertion  #}}}
# Tab Completion of Words  {{{#
class Completion_SimpleExample_ECR(_VimTest):
    snippets = ("test", "$1 ${1:blah}")
    keys = "superkallifragilistik\ntest" + EX + "sup" + COMPL_KW + \
            COMPL_ACCEPT + " some more"
    wanted = "superkallifragilistik\nsuperkallifragilistik some more " \
            "superkallifragilistik some more"

# We need >2 different words with identical starts to create the
# popup-menu:
COMPLETION_OPTIONS = "completion1\ncompletion2\n"

class Completion_ForwardsJumpWithoutCOMPL_ACCEPT(_VimTest):
    # completions should not be truncated when JF is activated without having
    # pressed COMPL_ACCEPT (Bug #598903)
    snippets = ("test", "$1 $2")
    keys = COMPLETION_OPTIONS + "test" + EX + "com" + COMPL_KW + JF + "foo"
    wanted = COMPLETION_OPTIONS + "completion1 foo"

class Completion_BackwardsJumpWithoutCOMPL_ACCEPT(_VimTest):
    # completions should not be truncated when JB is activated without having
    # pressed COMPL_ACCEPT (Bug #598903)
    snippets = ("test", "$1 $2")
    keys = COMPLETION_OPTIONS + "test" + EX + "foo" + JF + "com" + COMPL_KW + \
           JB + "foo"
    wanted = COMPLETION_OPTIONS + "foo completion1"
# End: Tab Completion of Words  #}}}
# Pressing BS in TabStop  {{{#
# Test for Bug #774917
class Backspace_TabStop_Zero(_VimTest):
    snippets = ("test", "A${1:C} ${0:DDD}", "This is Case 1")
    keys = "test" + EX + "A" + JF + BS + "BBB"
    wanted = "AA BBB"

class Backspace_TabStop_NotZero(_VimTest):
    snippets = ("test", "A${1:C} ${2:DDD}", "This is Case 1")
    keys = "test" + EX + "A" + JF + BS + "BBB"
    wanted = "AA BBB"
# End: Pressing BS in TabStop  #}}}
# Newline in default text {{{#
# Tests for bug 616315 #
class TrailingNewline_TabStop_NLInsideStuffBehind(_VimTest):
    snippets = ("test", r"""
x${1:
}<-behind1
$2<-behind2""")
    keys = "test" + EX + "j" + JF + "k"
    wanted = """
xj<-behind1
k<-behind2"""

class TrailingNewline_TabStop_JustNL(_VimTest):
    snippets = ("test", r"""
x${1:
}
$2""")
    keys = "test" + EX + "j" + JF + "k"
    wanted = """
xj
k"""

class TrailingNewline_TabStop_EndNL(_VimTest):
    snippets = ("test", r"""
x${1:a
}
$2""")
    keys = "test" + EX + "j" + JF + "k"
    wanted = """
xj
k"""

class TrailingNewline_TabStop_StartNL(_VimTest):
    snippets = ("test", r"""
x${1:
a}
$2""")
    keys = "test" + EX + "j" + JF + "k"
    wanted = """
xj
k"""

class TrailingNewline_TabStop_EndStartNL(_VimTest):
    snippets = ("test", r"""
x${1:
a
}
$2""")
    keys = "test" + EX + "j" + JF + "k"
    wanted = """
xj
k"""

class TrailingNewline_TabStop_NotEndStartNL(_VimTest):
    snippets = ("test", r"""
x${1:a
a}
$2""")
    keys = "test" + EX + "j" + JF + "k"
    wanted = """
xj
k"""

class TrailingNewline_TabStop_ExtraNL_ECR(_VimTest):
    snippets = ("test", r"""
x${1:a
a}
$2
""")
    keys = "test" + EX + "j" + JF + "k"
    wanted = """
xj
k
"""

class _MultiLineDefault(_VimTest):
    snippets = ("test", r"""
x${1:a
b
c
d
e
f}
$2""")

class MultiLineDefault_Jump(_MultiLineDefault):
    keys = "test" + EX + JF + "y"
    wanted = """
xa
b
c
d
e
f
y"""

class MultiLineDefault_Type(_MultiLineDefault):
    keys = "test" + EX + "z" + JF + "y"
    wanted = """
xz
y"""

class MultiLineDefault_BS(_MultiLineDefault):
    keys = "test" + EX + BS + JF + "y"
    wanted = """
x
y"""



# End: Newline in default text  #}}}
# Quotes in Snippets  {{{#
# Test for Bug #774917
def _snip_quote(qt):
    return (
            ("te" + qt + "st", "Expand me" + qt + "!", "test: "+qt),
            ("te", "Bad", ""),
            )

class Snippet_With_SingleQuote(_VimTest):
    snippets = _snip_quote("'")
    keys = "te'st" + EX
    wanted = "Expand me'!"

class Snippet_With_SingleQuote_List(_VimTest):
    snippets = _snip_quote("'")
    keys = "te" + LS + "2\n"
    wanted = "Expand me'!"

class Snippet_With_DoubleQuote(_VimTest):
    snippets = _snip_quote('"')
    keys = 'te"st' + EX
    wanted = "Expand me\"!"

class Snippet_With_DoubleQuote_List(_VimTest):
    snippets = _snip_quote('"')
    keys = "te" + LS + "2\n"
    wanted = "Expand me\"!"
# End: Quotes in Snippets  #}}}
# Umlauts and Special Chars  {{{#
class _UmlautsBase(_VimTest):
    skip_if = lambda self: running_on_windows()  # SendKeys can't send UTF characters

class Snippet_With_Umlauts_List(_UmlautsBase):
    snippets = _snip_quote('ü')
    keys = 'te' + LS + "2\n"
    wanted = "Expand meü!"

class Snippet_With_Umlauts(_UmlautsBase):
    snippets = _snip_quote('ü')
    keys = 'teüst' + EX
    wanted = "Expand meü!"

class Snippet_With_Umlauts_TypeOn(_UmlautsBase):
    snippets = ('ül', 'üüüüüßßßß')
    keys = 'te ül' + EX + "more text"
    wanted = "te üüüüüßßßßmore text"
class Snippet_With_Umlauts_OverwriteFirst(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü ${2:hello}ßß\nüüüü')
    keys = 'te ül' + EX + "more text" + JF + JF + "end"
    wanted = "te üü more text üü helloßß\nüüüüend"
class Snippet_With_Umlauts_OverwriteSecond(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü ${2:hello}ßß\nüüüü')
    keys = 'te ül' + EX + JF + "more text" + JF + "end"
    wanted = "te üü world üü more textßß\nüüüüend"
class Snippet_With_Umlauts_OverwriteNone(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü ${2:hello}ßß\nüüüü')
    keys = 'te ül' + EX + JF + JF + "end"
    wanted = "te üü world üü helloßß\nüüüüend"
class Snippet_With_Umlauts_Mirrors(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü $1')
    keys = 'te ül' + EX + "hello"
    wanted = "te üü hello üü hello"
class Snippet_With_Umlauts_Python(_UmlautsBase):
    snippets = ('ül', 'üü ${1:world} üü `!p snip.rv = len(t[1])*"a"`')
    keys = 'te ül' + EX + "hüüll"
    wanted = "te üü hüüll üü aaaaa"
# End: Umlauts and Special Chars  #}}}
# Exclusive Selection  {{{#
class _ES_Base(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set selection=exclusive")
class ExclusiveSelection_SimpleTabstop_Test(_ES_Base):
    snippets = ("test", "h${1:blah}w $1")
    keys = "test" + EX + "ui" + JF
    wanted = "huiw ui"

class ExclusiveSelection_RealWorldCase_Test(_ES_Base):
    snippets = ("for",
"""for ($${1:i} = ${2:0}; $$1 < ${3:count}; $$1${4:++}) {
	${5:// code}
}""")
    keys = "for" + EX + "k" + JF
    wanted = """for ($k = 0; $k < count; $k++) {
	// code
}"""
# End: Exclusive Selection  #}}}

# Old Selection {{{#
class _OS_Base(_VimTest):
    def _extra_options_pre_init(self, vim_config):
        vim_config.append("set selection=old")
class OldSelection_SimpleTabstop_Test(_OS_Base):
    snippets =("test", "h${1:blah}w $1")
    keys = "test" + EX + "ui" + JF
    wanted = "huiw ui"

class OldSelection_RealWorldCase_Test(_OS_Base):
    snippets = ("for",
"""for ($${1:i} = ${2:0}; $$1 < ${3:count}; $$1${4:++}) {
	${5:// code}
}""")
    keys = "for" + EX + "k" + JF
    wanted = """for ($k = 0; $k < count; $k++) {
	// code
}"""
# End: Old Selection #}}}

# Normal mode editing  {{{#
# Test for bug #927844
class DeleteLastTwoLinesInSnippet(_VimTest):
    snippets = ("test", "$1hello\nnice\nworld")
    keys = "test" + EX + ESC + "j2dd"
    wanted = "hello"
class DeleteCurrentTabStop1_JumpBack(_VimTest):
    snippets = ("test", "${1:hi}\nend")
    keys = "test" + EX + ESC + "ddi" + JB
    wanted = "end"
class DeleteCurrentTabStop2_JumpBack(_VimTest):
    snippets = ("test", "${1:hi}\n${2:world}\nend")
    keys = "test" + EX + JF + ESC + "ddi" + JB + "hello"
    wanted = "hello\nend"
class DeleteCurrentTabStop3_JumpAround(_VimTest):
    snippets = ("test", "${1:hi}\n${2:world}\nend")
    keys = "test" + EX + JF + ESC + "ddkji" + JB + "hello" + JF + "world"
    wanted = "hello\nendworld"

# End: Normal mode editing  #}}}
# Test for bug 1251994  {{{#
class Bug1251994(_VimTest):
    snippets = ("test", "${2:#2} ${1:#1};$0")
    keys = "  test" + EX + "hello" + JF + "world" + JF + "blub"
    wanted = "  world hello;blub"
# End: 1251994  #}}}
# Test for https://github.com/SirVer/ultisnips/issues/157 (virtualedit) {{{#
class VirtualEdit(_VimTest):
    snippets = ("pd", "padding: ${1:0}px")
    keys = "\t\t\tpd" + EX + "2"
    wanted = "\t\t\tpadding: 2px"

    def _extra_options_pre_init(self, vim_config):
        vim_config.append('set virtualedit=all')
        vim_config.append('set noexpandtab')
# End: 1251994  #}}}
# Test for Github Pull Request #134 - Retain unnamed register {{{#
class RetainsTheUnnamedRegister(_VimTest):
    snippets = ("test", "${1:hello} ${2:world} ${0}")
    keys = "yank" + ESC + "by4lea test" + EX + "HELLO" + JF + JF + ESC + "p"
    wanted = "yank HELLO world yank"
class RetainsTheUnnamedRegister_ButOnlyOnce(_VimTest):
    snippets = ("test", "${1:hello} ${2:world} ${0}")
    keys = "blahfasel" + ESC + "v" + 4*ARR_L + "xotest" + EX + ESC + ARR_U + "v0xo" + ESC + "p"
    wanted = "\nblah\nhello world "
# End: Github Pull Request # 134 #}}}
# snipMate support  {{{#
class snipMate_SimpleSnippet(_VimTest):
    files = { "snippets/_.snippets": """
snippet hello
\tThis is a test snippet
\t# With a comment"""}
    keys = "hello" + EX
    wanted = "This is a test snippet\n# With a comment"
class snipMate_OtherFiletype(_VimTest):
    files = { "snippets/blubi.snippets": """
snippet hello
\tworked"""}
    keys = "hello" + EX + ESC + ":set ft=blubi\nohello" + EX
    wanted = "hello" + EX + "\nworked"
class snipMate_MultiMatches(_VimTest):
    files = { "snippets/_.snippets": """
snippet hello The first snippet."
\tone
snippet hello The second snippet.
\ttwo"""}
    keys = "hello" + EX + "2\n"
    wanted = "two"
class snipMate_SimpleSnippetSubDirectory(_VimTest):
    files = { "snippets/_/blub.snippets": """
snippet hello
\tThis is a test snippet"""}
    keys = "hello" + EX
    wanted = "This is a test snippet"
class snipMate_SimpleSnippetInSnippetFile(_VimTest):
    files = {
        "snippets/_/hello.snippet": """This is a stand alone snippet""",
        "snippets/_/hello1.snippet": """This is two stand alone snippet""",
        "snippets/_/hello2/this_is_my_cool_snippet.snippet": """Three""",
    }
    keys = "hello" + EX + "\nhello1" + EX + "\nhello2" + EX
    wanted = "This is a stand alone snippet\nThis is two stand alone snippet\nThree"
class snipMate_Interpolation(_VimTest):
    files = { "snippets/_.snippets": """
snippet test
\tla`printf('c%02d', 3)`lu"""}
    keys = "test" + EX
    wanted = "lac03lu"
class snipMate_InterpolationWithSystem(_VimTest):
    files = { "snippets/_.snippets": """
snippet test
\tla`system('echo -ne öäü')`lu"""}
    keys = "test" + EX
    wanted = "laöäülu"
class snipMate_TestMirrors(_VimTest):
    files = { "snippets/_.snippets": """
snippet for
\tfor (${2:i}; $2 < ${1:count}; $1++) {
\t\t${4}
\t}"""}
    keys = "for" + EX + "blub" + JF + "j" + JF + "hi"
    wanted = "for (j; j < blub; blub++) {\n\thi\n}"
class snipMate_TestMirrorsInPlaceholders(_VimTest):
    files = { "snippets/_.snippets": """
snippet opt
\t<option value="${1:option}">${2:$1}</option>"""}
    keys = "opt" + EX + "some" + JF + JF + "ende"
    wanted = """<option value="some">some</option>ende"""
class snipMate_TestMirrorsInPlaceholders_Overwrite(_VimTest):
    files = { "snippets/_.snippets": """
snippet opt
\t<option value="${1:option}">${2:$1}</option>"""}
    keys = "opt" + EX + "some" + JF + "not" + JF + "ende"
    wanted = """<option value="some">not</option>ende"""
class snipMate_Visual_Simple(_VimTest):
    files = { "snippets/_.snippets": """
snippet v
\th${VISUAL}b"""}
    keys = "blablub" + ESC + "0v6l" + EX + "v" + EX
    wanted = "hblablubb"
class snipMate_NoNestedTabstops(_VimTest):
    files = { "snippets/_.snippets": """
snippet test
\th$${1:${2:blub}}$$"""}
    keys = "test" + EX + JF + "hi"
    wanted = "h$${2:blub}$$hi"
class snipMate_Extends(_VimTest):
    files = { "snippets/a.snippets": """
extends b
snippet test
\tblub""", "snippets/b.snippets": """
snippet test1
\tblah"""
}
    keys = ESC + ":set ft=a\n" + "itest1" + EX
    wanted = "blah"
class snipMate_EmptyLinesContinueSnippets(_VimTest):
    files = { "snippets/_.snippets": """
snippet test
\tblub

\tblah

snippet test1
\ta"""
}
    keys = "test" + EX
    wanted = "blub\n\nblah\n"
class snipMate_OverwrittenByRegExpTrigger(_VimTest):
    files = { "snippets/_.snippets": """
snippet def
\tsnipmate
""",
    "us/all.snippets": r"""
snippet "(de)?f" "blub" r
ultisnips
endsnippet
""" }
    keys = "def" + EX
    wanted = "ultisnips"
# End: snipMate support  #}}}
# SnippetsInCurrentScope  {{{#
class VerifyVimDict1(_VimTest):
    """check:
    correct type (4 means vim dictionary)
    correct length of dictionary (in this case we have on element if the use same prefix, dictionary should have 1 element)
    correct description (including the apostrophe)
    if the prefix is mismatched no resulting dict should have 0 elements
    """

    snippets = ('testâ', 'abc123ά', '123\'êabc')
    keys = ('test=(type(UltiSnips#SnippetsInCurrentScope()) . len(UltiSnips#SnippetsInCurrentScope()) . ' +
       'UltiSnips#SnippetsInCurrentScope()["testâ"]' + ')\n' +
       '=len(UltiSnips#SnippetsInCurrentScope())\n')

    wanted = 'test41123\'êabc0'

class VerifyVimDict2(_VimTest):
    """check:
    can use " in trigger
    """

    snippets = ('te"stâ', 'abc123ά', '123êabc')
    akey = "'te{}stâ'".format('"')
    keys = ('te"=(UltiSnips#SnippetsInCurrentScope()[{}]'.format(akey) + ')\n')
    wanted = 'te"123êabc'

class VerifyVimDict3(_VimTest):
    """check:
    can use ' in trigger
    """

    snippets = ("te'stâ", 'abc123ά', '123êabc')
    akey = '"te{}stâ"'.format("'")
    keys = ("te'=(UltiSnips#SnippetsInCurrentScope()[{}]".format(akey) + ')\n')
    wanted = "te'123êabc"
# End: SnippetsInCurrentScope  #}}}
# Snippet Source  {{{#
class AddNewSnippetSource(_VimTest):
    keys = ( "blumba" + EX + ESC +
      ":%(python)s UltiSnips_Manager.register_snippet_source(" +
          "'temp', MySnippetSource())\n" +
      "oblumba" + EX + ESC +
      ":%(python)s UltiSnips_Manager.unregister_snippet_source('temp')\n" +
      "oblumba" + EX ) % { 'python': 'py3' if PYTHON3 else 'py' }
    wanted = (
      "blumba" + EX + "\n" +
      "this is a dynamic snippet" + "\n" +
      "blumba" + EX
    )

    def _extra_options_post_init(self, vim_config):
        self._create_file("snippet_source.py","""
from UltiSnips.snippet.source import SnippetSource
from UltiSnips.snippet.definition import UltiSnipsSnippetDefinition

class MySnippetSource(SnippetSource):
  def get_snippets(self, filetypes, before, possible):
    if before.endswith('blumba'):
      return [
          UltiSnipsSnippetDefinition(
              -100, "blumba", "this is a dynamic snippet", "", "", {}, "blub")
        ]
    return []
""")
        pyfile = 'py3file' if PYTHON3 else 'pyfile'
        vim_config.append("%s %s" % (pyfile, os.path.join(
            self._temporary_directory, "snippet_source.py")))
# End: Snippet Source  #}}}

# Plugin: YouCompleteMe  {{{#
class Plugin_YouCompleteMe_IntegrationTest(_VimTest):
    def skip_if(self):
        r = python3()
        if r:
            return r
        if "7.4" not in self.version:
            return "Needs Vim 7.4."
    plugins = ["Valloric/YouCompleteMe"]
    snippets = ("superlongtrigger", "Hello")
    keys = "superlo\ty"
    wanted = "Hello"

    def _extra_options_pre_init(self, vim_config):
        # Not sure why, but I need to make a new tab for this to work.
        vim_config.append('let g:UltiSnipsExpandTrigger="y"')
        vim_config.append('tabnew')

    def _before_test(self):
        self.vim.send(":set ft=python\n")
        # Give ycm a chance to catch up.
        time.sleep(1)
# End: Plugin: YouCompleteMe  #}}}
# Plugin: Neocomplete {{{#
class Plugin_Neocomplete_BugTest(_VimTest):
    # Test for https://github.com/SirVer/ultisnips/issues/228
    def skip_if(self):
        if "+lua" not in self.version:
            return "Needs +lua"
    plugins = ["Shougo/neocomplete.vim"]
    snippets = ("t", "Hello", "", "w")
    keys = "iab\\ t" + EX
    wanted = "iab\\ Hello"

    def _extra_options_pre_init(self, vim_config):
        vim_config.append(r'set iskeyword+=\\ ')
        vim_config.append('let g:neocomplete#enable_at_startup = 1')
        vim_config.append('let g:neocomplete#enable_smart_case = 1')
        vim_config.append('let g:neocomplete#enable_camel_case = 1')
        vim_config.append('let g:neocomplete#enable_auto_delimiter = 1')
        vim_config.append('let g:neocomplete#enable_refresh_always = 1')
# End: Plugin: Neocomplete  #}}}
# Plugin: unite {{{#
class Plugin_unite_BugTest(_VimTest):
    plugins = ["Shougo/unite.vim"]
    snippets = ("t", "Hello", "", "w")
    keys = "iab\\ t=UltiSnipsCallUnite()\n"
    wanted = "iab\\ Hello "

    def _extra_options_pre_init(self, vim_config):
        vim_config.append(r'set iskeyword+=\\ ')
        vim_config.append('function! UltiSnipsCallUnite()')
        vim_config.append('  Unite -start-insert -winheight=100 -immediately -no-empty ultisnips')
        vim_config.append('  return ""')
        vim_config.append('endfunction')
# End: Plugin: unite  #}}}
# Plugin: Supertab {{{#
class Plugin_SuperTab_SimpleTest(_VimTest):
    plugins = ["ervandew/supertab"]
    snippets = ("long", "Hello", "", "w")
    keys = ( "longtextlongtext\n" +
        "longt" + EX + "\n" +  # Should complete word
        "long" + EX )  # Should expand
    wanted = "longtextlongtext\nlongtextlongtext\nHello"

    def _before_test(self):
        # Make sure that UltiSnips has the keymap
        self.vim.send(":call UltiSnips#map_keys#MapKeys()\n")

    def _extra_options_post_init(self, vim_config):
        assert EX == "\t"  # Otherwise this test needs changing.
        vim_config.append('let g:SuperTabDefaultCompletionType = "<c-p>"')
        vim_config.append('let g:SuperTabRetainCompletionDuration = "insert"')
        vim_config.append('let g:SuperTabLongestHighlight = 1')
        vim_config.append('let g:SuperTabCrMapping = 0')
# End: Plugin: Supertab   #}}}

###########################################################################
#                               END OF TEST                               #
###########################################################################


if __name__ == '__main__':
    import sys
    import optparse

    def parse_args():
        p = optparse.OptionParser("%prog [OPTIONS] <test case names to run>")

        p.set_defaults(session="vim", interrupt=False,
                verbose=False, interface="screen", retries=4, plugins=False)

        p.add_option("-v", "--verbose", dest="verbose", action="store_true",
            help="print name of tests as they are executed")
        p.add_option("--clone-plugins", action="store_true",
            help="Only clones dependant plugins and exits the test runner.")
        p.add_option("--plugins", action="store_true",
            help="Run integration tests with other Vim plugins.")
        p.add_option("--interface", type=str,
                help="interface to vim to use on Mac and or Linux [screen|tmux].")
        p.add_option("-s", "--session", dest="session",  metavar="SESSION",
            help="session parameters for the terminal multiplexer SESSION [%default]")
        p.add_option("-i", "--interrupt", dest="interrupt",
            action="store_true",
            help="Stop after defining the snippet. This allows the user " \
             "to interactively test the snippet in vim. You must give " \
             "exactly one test case on the cmdline. The test will always fail."
        )
        p.add_option("-r", "--retries", dest="retries", type=int,
                help="How often should each test be retried before it is "
                "considered failed. Works around flakyness in the terminal "
                "multiplexer and race conditions in writing to the file system.")

        o, args = p.parse_args()
        if o.interface not in ("screen", "tmux"):
            p.error("--interface must be [screen|tmux].")

        return o, args

    def main():
        options,selected_tests = parse_args()

        test_loader = unittest.TestLoader()
        all_test_suites = test_loader.loadTestsFromModule(__import__("test"))

        vim = None
        if not options.clone_plugins:
            if platform.system() == "Windows":
                raise RuntimeError("TODO: TestSuite is broken under windows. Volunteers wanted!.")
                # vim = VimInterfaceWindows()
                vim.focus()
            else:
                if options.interface == "screen":
                    vim = VimInterfaceScreen(options.session)
                elif options.interface == "tmux":
                    vim = VimInterfaceTmux(options.session)

        suite = unittest.TestSuite()
        all_other_plugins = set()
        for s in all_test_suites:
            for test in s:
                test.interrupt = options.interrupt
                test.retries = options.retries
                test.test_plugins = options.plugins
                test.vim = vim
                all_other_plugins.update(test.plugins)

                if len(selected_tests):
                    id = test.id().split('.')[1]
                    if not any([ id.startswith(t) for t in selected_tests ]):
                        continue
                suite.addTest(test)

        if options.plugins or options.clone_plugins:
            setup_other_plugins(all_other_plugins)
            if options.clone_plugins:
                return

        if options.verbose:
            v = 2
        else:
            v = 1
        res = unittest.TextTestRunner(verbosity=v).run(suite)

    main()

# vim:fileencoding=utf-8:foldmarker={{{#,#}}}:
