#!/usr/bin/env python
# encoding: utf-8

"""Implements `echo hi` shell code interpolation."""

import os
import platform
from subprocess import Popen, PIPE
import stat
import tempfile

from UltiSnips.text_objects.base import NoneditableTextObject


def _chomp(string):
    """Rather than rstrip(), remove only the last newline and preserve
    purposeful whitespace."""
    if len(string) and string[-1] == "\n":
        string = string[:-1]
    if len(string) and string[-1] == "\r":
        string = string[:-1]
    return string


def _run_shell_command(cmd, tmpdir):
    """Write the code to a temporary file."""
    cmdsuf = ""
    if platform.system() == "Windows":
        # suffix required to run command on windows
        cmdsuf = ".bat"
        # turn echo off
        cmd = "@echo off\r\n" + cmd
    handle, path = tempfile.mkstemp(text=True, dir=tmpdir, suffix=cmdsuf)
    os.write(handle, cmd.encode("utf-8"))
    os.close(handle)
    os.chmod(path, stat.S_IRWXU)

    # Execute the file and read stdout
    proc = Popen(path, shell=True, stdout=PIPE, stderr=PIPE)
    proc.wait()
    stdout, _ = proc.communicate()
    os.unlink(path)
    return _chomp(stdout.decode("utf-8"))


def _get_tmp():
    """Find an executable tmp directory."""
    userdir = os.path.expanduser("~")
    for testdir in [
        tempfile.gettempdir(),
        os.path.join(userdir, ".cache"),
        os.path.join(userdir, ".tmp"),
        userdir,
    ]:
        if (
            not os.path.exists(testdir)
            or not _run_shell_command("echo success", testdir) == "success"
        ):
            continue
        return testdir
    return ""


class ShellCode(NoneditableTextObject):

    """See module docstring."""

    def __init__(self, parent, token):
        NoneditableTextObject.__init__(self, parent, token)
        self._code = token.code.replace("\\`", "`")
        self._tmpdir = _get_tmp()

    def _update(self, done, buf):
        if not self._tmpdir:
            output = "Unable to find executable tmp directory, check noexec on /tmp"
        else:
            output = _run_shell_command(self._code, self._tmpdir)
        self.overwrite(buf, output)
        self._parent._del_child(self)  # pylint:disable=protected-access
        return True
