# encoding: utf-8

import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import time

from test.constant import (ARR_D, ARR_L, ARR_R, ARR_U, BS, ESC, PYTHON3,
                           SEQUENCES)


def wait_until_file_exists(file_path, times=None, interval=0.01):
    while times is None or times:
        if os.path.exists(file_path):
            return True
        time.sleep(interval)
        if times is not None:
            times -= 1
    return False


def read_text_file(filename):
    """Reads the contens of a text file."""
    if PYTHON3:
        return open(filename, 'r', encoding='utf-8').read()
    else:
        return open(filename, 'r').read()


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


class TempFileManager(object):

    def __init__(self, name=''):
        self._temp_dir = tempfile.mkdtemp(prefix='UltiSnipsTest_' + name)

    def name_temp(self, file_path):
        return os.path.join(self._temp_dir, file_path)

    def write_temp(self, file_path, content):
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
        file_handler, abspath = tempfile.mkstemp(
            suffix, prefix, self._temp_dir)
        os.close(file_handler)
        os.remove(abspath)
        return abspath

    def clear_temp(self):
        shutil.rmtree(self._temp_dir)
        create_directory(self._temp_dir)


class VimInterface(TempFileManager):

    def __init__(self, vim_executable, name):
        TempFileManager.__init__(self, name)
        self._vim_executable = vim_executable
        self._patch_version = None

    def has_patch(self, version):
        if self._patch_version is None:
            output = subprocess.check_output([
                self._vim_executable, "--version"
            ])

            self._patch_version = 0
            for line in output.decode('utf-8').split("\n"):
                if line.startswith("Included patches:"):
                    self._patch_version = line.split('-')[1]

        return int(self._patch_version) >= version

    def get_buffer_data(self):
        buffer_path = self.unique_name_temp(prefix='buffer_')
        self.send_to_vim(ESC + ':w! %s\n' % buffer_path)
        if wait_until_file_exists(buffer_path, 50):
            return read_text_file(buffer_path)[:-1]

    def send_to_terminal(self, s):
        """Types 's' into the terminal."""
        raise NotImplementedError()

    def send_to_vim(self, s):
        """Types 's' into the vim instance under test."""
        raise NotImplementedError()

    def launch(self, config=[]):
        """Returns the python version in Vim as a string, e.g. '2.7'"""
        pid_file = self.name_temp('vim.pid')
        done_file = self.name_temp('loading_done')
        if os.path.exists(done_file):
            os.remove(done_file)

        post_config = []
        post_config.append('%s << EOF' % ('py3' if PYTHON3 else 'py'))
        post_config.append('import vim, sys')
        post_config.append(
            "with open('%s', 'w') as pid_file: pid_file.write(vim.eval('getpid()'))" %
            pid_file)
        post_config.append("with open('%s', 'w') as done_file:" % done_file)
        post_config.append("    done_file.write('%i.%i.%i' % sys.version_info[:3])")
        post_config.append('EOF')

        config_path = self.write_temp('vim_config.vim',
                                      textwrap.dedent(os.linesep.join(config + post_config) + '\n'))

        # Note the space to exclude it from shell history. Also we always set
        # NVIM_LISTEN_ADDRESS, even when running vanilla Vim, because it will
        # just not care.
        self.send_to_terminal(""" NVIM_LISTEN_ADDRESS=/tmp/nvim %s -u %s\r\n""" % (
            self._vim_executable, config_path))
        wait_until_file_exists(done_file)
        self._vim_pid = int(read_text_file(pid_file))
        return read_text_file(done_file).strip()

    def leave_with_wait(self):
        self.send_to_vim(3 * ESC + ':qa!\n')
        while is_process_running(self._vim_pid):
            time.sleep(.2)


class VimInterfaceTmux(VimInterface):

    def __init__(self, vim_executable, session):
        VimInterface.__init__(self, vim_executable, 'Tmux')
        self.session = session
        self._check_version()

    def _send(self, s):
        # I did not find any documentation on what needs escaping when sending
        # to tmux, but it seems like this is all that is needed for now.
        s = s.replace(';', r'\;')

        if PYTHON3:
            s = s.encode('utf-8')
        silent_call(['tmux', 'send-keys', '-t', self.session, '-l', s])

    def send_to_terminal(self, s):
        return self._send(s)

    def send_to_vim(self, s):
        return self._send(s)

    def _check_version(self):
        stdout, _ = subprocess.Popen(['tmux', '-V'],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if PYTHON3:
            stdout = stdout.decode('utf-8')
        m = re.match(r"tmux (\d+).(\d+)", stdout)
        if not m or not (int(m.group(1)), int(m.group(2))) >= (1, 8):
            raise RuntimeError(
                'Need at least tmux 1.8, you have %s.' %
                stdout.strip())

class VimInterfaceTmuxNeovim(VimInterfaceTmux):

    def __init__(self, vim_executable, session):
        VimInterfaceTmux.__init__(self, vim_executable, session)
        self._nvim = None

    def send_to_vim(self, s):
        if s == ARR_L:
            s = "<Left>"
        elif s == ARR_R:
            s = "<Right>"
        elif s == ARR_U:
            s = "<Up>"
        elif s == ARR_D:
            s = "<Down>"
        elif s == BS:
            s = "<bs>"
        elif s == ESC:
            s = "<esc>"
        elif s == "<":
            s = "<lt>"
        self._nvim.input(s)

    def launch(self, config=[]):
        import neovim
        rv = VimInterfaceTmux.launch(self, config)
        self._nvim = neovim.attach('socket', path='/tmp/nvim')
        return rv

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
        keys = self.convert_keys(keys)

        if not self.is_focused():
            time.sleep(2)
            self.focus()
        if not self.is_focused():
            # This is the only way I can find to stop test execution
            raise KeyboardInterrupt('Failed to focus GVIM')

        self.shell.SendKeys(keys)
