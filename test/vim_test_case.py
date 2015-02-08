# encoding: utf-8

# pylint: skip-file

import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import time
import unittest
from test.constant import (ARR_D, ARR_L, ARR_R, ARR_U, BS, ESC, PYTHON3,
                           SEQUENCES)


def is_process_running(pid):
    """Returns true if a process with pid is running, false otherwise."""
    # from
    # http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
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
    return os.path.join(tempfile.gettempdir(), 'UltiSnips_test_vim_plugins')


def read_text_file(filename):
    """Reads the contens of a text file."""
    if PYTHON3:
        return open(filename, 'r', encoding='utf-8').read()
    else:
        return open(filename, 'r').read()


def wait_until_file_exists(file_path, times=None, interval=0.01):
    while times is None or times:
        if os.path.exists(file_path):
            return True
        time.sleep(interval)
        if times is not None:
            times -= 1
    return False


class TempFileManager(object):

    """A TempFileManager keeps a unique prefix path for temp files.

    A temp file, or a name for a temp file generate by a TempFileManager
    always belongs to the same directory.

    """

    def __init__(self, name=''):
        """The unique prefix path is UltiSnipsTest_{name}XXXXXX."""
        self._temp_dir = tempfile.mkdtemp(prefix='UltiSnipsTest_' + name)

    def name_temp(self, file_path):
        """Get the absolute path of a temp file by given file path."""
        return os.path.join(self._temp_dir, file_path)

    def write_temp(self, file_path, content):
        """Write the content to a temp file by given file path inside the
        _temp_dir, and return the absolute path of that file."""
        abs_path = self.name_temp(file_path)
        create_directory(os.path.dirname(abs_path))
        if PYTHON3:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            with open(abs_path, 'w') as f:
                f.write(content)
        return abs_path

    def unique_name_temp(self, suffix='', prefix=''):
        """Generate a unique name for a temp file with given suffix and prefix,
        and return full absolute path."""
        file_handler, abspath = tempfile.mkstemp(
            suffix, prefix, self._temp_dir)
        os.close(file_handler)
        os.remove(abspath)
        return abspath

    def clear_temp(self):
        """Clear the temp file directory, but the directory itself is not
        removed."""
        shutil.rmtree(self._temp_dir)
        create_directory(self._temp_dir)


class VimInterface(TempFileManager):

    def __init__(self, name=''):
        TempFileManager.__init__(self, name)

    def get_buffer_data(self):
        buffer_path = self.unique_name_temp(prefix='buffer_')
        self.send(ESC + ':w! %s\n' % buffer_path)
        if wait_until_file_exists(buffer_path, 50):
            return read_text_file(buffer_path)[:-1]

    def send(self, s):
        raise NotImplementedError()

    def launch(self, config=[]):
        pid_file = self.name_temp('vim.pid')
        done_file = self.name_temp('loading_done')
        if os.path.exists(done_file):
            os.remove(done_file)

        post_config = []
        post_config.append('%s << EOF' % ('py3' if PYTHON3 else 'py'))
        post_config.append('import vim')
        post_config.append(
            "with open('%s', 'w') as pid_file: pid_file.write(vim.eval('getpid()'))" %
            pid_file)
        post_config.append(
            "with open('%s', 'w') as done_file: pass" %
            done_file)
        post_config.append('EOF')

        config_path = self.write_temp('vim_config.vim',
                                      textwrap.dedent(os.linesep.join(config + post_config) + '\n'))

        # Note the space to exclude it from shell history.
        self.send(""" vim -u %s\r\n""" % config_path)
        wait_until_file_exists(done_file)
        self._vim_pid = int(open(pid_file, 'r').read())

    def leave_with_wait(self):
        self.send(3 * ESC + ':qa!\n')
        while is_process_running(self._vim_pid):
            time.sleep(.05)


class VimInterfaceScreen(VimInterface):

    def __init__(self, session):
        VimInterface.__init__(self, 'Screen')
        self.session = session
        self.need_screen_escapes = 0
        self.detect_parsing()

    def send(self, s):
        if self.need_screen_escapes:
            # escape characters that are special to some versions of screen
            repl = lambda m: '\\' + m.group(0)
            s = re.sub(r"[$^#\\']", repl, s)

        if PYTHON3:
            s = s.encode('utf-8')

        while True:
            rv = 0
            if len(s) > 30:
                rv |= silent_call(
                    ['screen', '-x', self.session, '-X', 'register', 'S', s])
                rv |= silent_call(
                    ['screen', '-x', self.session, '-X', 'paste', 'S'])
            else:
                rv |= silent_call(
                    ['screen', '-x', self.session, '-X', 'stuff', s])
            if not rv:
                break
            time.sleep(.2)

    def detect_parsing(self):
        self.launch()
        # Send a string where the interpretation will depend on version of
        # screen
        string = '$TERM'
        self.send('i' + string + ESC)
        output = self.get_buffer_data()
        # If the output doesn't match the input, need to do additional escaping
        if output != string:
            self.need_screen_escapes = 1
        self.leave_with_wait()


class VimInterfaceTmux(VimInterface):

    def __init__(self, session):
        self.session = session
        self._check_version()

    def send(self, s):
        # I did not find any documentation on what needs escaping when sending
        # to tmux, but it seems like this is all that is needed for now.
        s = s.replace(';', r'\;')

        if PYTHON3:
            s = s.encode('utf-8')
        silent_call(['tmux', 'send-keys', '-t', self.session, '-l', s])

    def _check_version(self):
        stdout, _ = subprocess.Popen(['tmux', '-V'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if PYTHON3:
            stdout = stdout.decode('utf-8')
        m = re.match(r"tmux (\d+).(\d+)", stdout)
        if not m or not (int(m.group(1)), int(m.group(2))) >= (1, 9):
            raise RuntimeError(
                'Need at least tmux 1.9, you have %s.' %
                stdout.strip())


class VimInterfaceWindows(VimInterface):
    BRACES = re.compile('([}{])')
    WIN_ESCAPES = ['+', '^', '%', '~', '[', ']', '<', '>', '(', ')']
    WIN_REPLACES = [
        (BS, '{BS}'),
        (ARR_L, '{LEFT}'),
        (ARR_R, '{RIGHT}'),
        (ARR_U, '{UP}'),
        (ARR_D, '{DOWN}'),
        ('\t', '{TAB}'),
        ('\n', '~'),
        (ESC, '{ESC}'),

        # On my system ` waits for a second keystroke, so `+SPACE = "`".  On
        # most systems, `+Space = "` ". I work around this, by sending the host
        # ` as `+_+BS. Awkward, but the only way I found to get this working.
        ('`', '`_{BS}'),
        ('´', '´_{BS}'),
        ('{^}', '{^}_{BS}'),
    ]

    def __init__(self):
        self.seq_buf = []
        # import windows specific modules
        import win32com.client
        import win32gui
        self.win32gui = win32gui
        self.shell = win32com.client.Dispatch('WScript.Shell')

    def is_focused(self, title=None):
        cur_title = self.win32gui.GetWindowText(
            self.win32gui.GetForegroundWindow())
        if (title or '- GVIM') in cur_title:
            return True
        return False

    def focus(self, title=None):
        if not self.shell.AppActivate(title or '- GVIM'):
            raise Exception('Failed to switch to GVim window')
        time.sleep(1)

    def convert_keys(self, keys):
        keys = self.BRACES.sub(r"{\1}", keys)
        for k in self.WIN_ESCAPES:
            keys = keys.replace(k, '{%s}' % k)
        for f, r in self.WIN_REPLACES:
            keys = keys.replace(f, r)
        return keys

    def send(self, keys):
        self.seq_buf.append(keys)
        seq = ''.join(self.seq_buf)

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
            raise KeyboardInterrupt('Failed to focus GVIM')

        self.shell.SendKeys(seq)


class VimTestCase(unittest.TestCase, TempFileManager):
    snippets = ()
    files = {}
    text_before = ' --- some text before --- \n\n'
    text_after = '\n\n --- some text after --- '
    expected_error = ''
    wanted = ''
    keys = ''
    sleeptime = 0.00
    output = ''
    plugins = []
    # Skip this test for the given reason or None for not skipping it.
    skip_if = lambda self: None
    version = None  # Will be set to vim --version output

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        TempFileManager.__init__(self, 'Case')

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
        """Send these keys before the test runs.

        Used for buffer local variables and other options.

        """

    def _create_file(self, file_path, content):
        """Creates a file in the runtimepath that is created for this test.

        Returns the absolute path to the file.

        """
        return self.write_temp(file_path, textwrap.dedent(content + '\n'))

    def _link_file(self, source, relative_destination):
        """Creates a link from 'source' to the 'relative_destination' in our
        temp dir."""
        absdir = self.name_temp(relative_destination)
        create_directory(absdir)
        os.symlink(source, os.path.join(absdir, os.path.basename(source)))

    def setUp(self):
        if not VimTestCase.version:
            VimTestCase.version, _ = subprocess.Popen(['vim', '--version'],
                                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            if PYTHON3:
                VimTestCase.version = VimTestCase.version.decode('utf-8')

        if self.plugins and not self.test_plugins:
            return self.skipTest('Not testing integration with other plugins.')
        reason_for_skipping = self.skip_if()
        if reason_for_skipping is not None:
            return self.skipTest(reason_for_skipping)

        vim_config = []
        vim_config.append('set nocompatible')
        vim_config.append('set runtimepath=$VIMRUNTIME,%s,%s' % (
            os.path.dirname(os.path.dirname(__file__)), self._temp_dir))

        if self.plugins:
            self._link_file(
                os.path.join(
                    plugin_cache_dir(),
                    'vim-pathogen',
                    'autoload'),
                '.')
            for plugin in self.plugins:
                self._link_file(
                    os.path.join(
                        plugin_cache_dir(),
                        os.path.basename(plugin)),
                    'bundle')
            vim_config.append('execute pathogen#infect()')

        # Vim parameters.
        vim_config.append('syntax on')
        vim_config.append('filetype plugin indent on')
        vim_config.append('set clipboard=""')
        vim_config.append('set encoding=utf-8')
        vim_config.append('set fileencoding=utf-8')
        vim_config.append('set buftype=nofile')
        vim_config.append('set shortmess=at')
        vim_config.append('let @" = ""')
        vim_config.append('let g:UltiSnipsExpandTrigger="<tab>"')
        vim_config.append('let g:UltiSnipsJumpForwardTrigger="?"')
        vim_config.append('let g:UltiSnipsJumpBackwardTrigger="+"')
        vim_config.append('let g:UltiSnipsListSnippets="@"')
        vim_config.append(
            'let g:UltiSnipsUsePythonVersion="%i"' %
            (3 if PYTHON3 else 2))
        vim_config.append('let g:UltiSnipsSnippetDirectories=["us"]')

        self._extra_options_pre_init(vim_config)

        # Now activate UltiSnips.
        vim_config.append('call UltiSnips#bootstrap#Bootstrap()')

        self._extra_options_post_init(vim_config)

        # Finally, add the snippets and some configuration for the test.
        vim_config.append('%s << EOF' % ('py3' if PYTHON3 else 'py'))

        if len(self.snippets) and not isinstance(self.snippets[0], tuple):
            self.snippets = (self.snippets, )
        for s in self.snippets:
            sv, content = s[:2]
            description = ''
            options = ''
            priority = 0
            if len(s) > 2:
                description = s[2]
            if len(s) > 3:
                options = s[3]
            if len(s) > 4:
                priority = s[4]
            vim_config.append('UltiSnips_Manager.add_snippet(%r, %r, %r, %r, priority=%i)' % (
                sv, content, description, options, priority))

        # fill buffer with default text and place cursor in between.
        prefilled_text = (self.text_before + self.text_after).splitlines()
        vim_config.append('vim.current.buffer[:] = %r\n' % prefilled_text)
        vim_config.append(
            'vim.current.window.cursor = (max(len(vim.current.buffer)//2, 1), 0)')

        # End of python stuff.
        vim_config.append('EOF')

        for name, content in self.files.items():
            self._create_file(name, content)

        self.vim.launch(vim_config)

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
            print('Working directory: %s' % (self._temp_dir))
            return
        self.vim.leave_with_wait()
        self.clear_temp()

# vim:fileencoding=utf-8:foldmarker={{{#,#}}}:
