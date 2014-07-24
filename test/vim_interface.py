# encoding: utf-8

import os
import re
import subprocess
import tempfile
import textwrap
import time

from test.constant import *

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
        return open(filename,"r", encoding="utf-8").read()
    else:
        return open(filename,"r").read()


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


class TempFileManager(object):
    def __init__(self, name=""):
        self._temp_dir = tempfile.mkdtemp(prefix="UltiSnipsTest_" + name)

    def name_temp(self, file_path):
        return os.path.join(self._temp_dir, file_path)

    def write_temp(self, file_path, content):
        abs_path = self.name_temp(file_path)
        create_directory(os.path.dirname(abs_path))
        if PYTHON3:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            with open(abs_path, "w") as f:
                f.write(content)
        return abs_path

    def unique_name_temp(self, suffix="", prefix=""):
        file_handler, abspath = tempfile.mkstemp(suffix, prefix, self._temp_dir)
        os.close(file_handler)
        os.remove(abspath)
        return abspath

    def clear_temp(self):
        shutil.rmtree(self._temp_dir)
        create_directory(self._temp_dir)


class VimInterface(TempFileManager):
    def __init__(self, name=""):
        TempFileManager.__init__(self, name)

    def get_buffer_data(self):
        buffer_path = self.unique_name_temp(prefix="buffer_")
        self.send(ESC + ":w! %s\n" % buffer_path)
        if wait_until_file_exists(buffer_path, 50):
            return read_text_file(buffer_path)[:-1]

    def send(self, s):
        raise NotImplementedError()

    def launch(self, config=[]):
        pid_file = self.name_temp("vim.pid")
        done_file = self.name_temp("loading_done")
        if os.path.exists(done_file):
            os.remove(done_file)

        post_config = []
        post_config.append("%s << EOF" % ("py3" if PYTHON3 else "py"))
        post_config.append("import vim")
        post_config.append("with open('%s', 'w') as pid_file: pid_file.write(vim.eval('getpid()'))" % pid_file)
        post_config.append("with open('%s', 'w') as done_file: pass" % done_file)
        post_config.append("EOF")

        config_path = self.write_temp("vim_config.vim",
                textwrap.dedent(os.linesep.join(config + post_config) + "\n"))

        # Note the space to exclude it from shell history.
        self.send(""" vim -u %s\r\n""" % config_path)
        wait_until_file_exists(done_file)
        self._vim_pid = int(open(pid_file, "r").read())

    def leave_with_wait(self):
        self.send(3*ESC + ":qa!\n")
        while is_process_running(self._vim_pid):
            time.sleep(.05)


class VimInterfaceScreen(VimInterface):
    def __init__(self, session):
        VimInterface.__init__(self, "Screen")
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
        self.launch()
        # Send a string where the interpretation will depend on version of screen
        string = "$TERM"
        self.send("i" + string + ESC)
        output = self.get_buffer_data()
        # If the output doesn't match the input, need to do additional escaping
        if output != string:
            self.need_screen_escapes = 1
        self.leave_with_wait()

class VimInterfaceTmux(VimInterface):
    def __init__(self, session):
        VimInterface.__init__(self, "Tmux")
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
        if not m or not (int(m.group(1)), int(m.group(2))) >= (1, 8):
            raise RuntimeError("Need at least tmux 1.8, you have %s." % stdout.strip())

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

