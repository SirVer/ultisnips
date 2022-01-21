# coding=utf8

from functools import wraps
import traceback
import re
import sys
import time
from bdb import BdbQuit

from UltiSnips import vim_helper
from UltiSnips.error import PebkacError
from UltiSnips.remote_pdb import RemotePDB


def _report_exception(self, msg, e):
    if hasattr(e, "snippet_info"):
        msg += "\nSnippet, caused error:\n"
        msg += re.sub(r"^(?=\S)", "  ", e.snippet_info, flags=re.MULTILINE)
    # snippet_code comes from _python_code.py, it's set manually for
    # providing error message with stacktrace of failed python code
    # inside of the snippet.
    if hasattr(e, "snippet_code"):
        _, _, tb = sys.exc_info()
        tb_top = traceback.extract_tb(tb)[-1]
        msg += "\nExecuted snippet code:\n"
        lines = e.snippet_code.split("\n")
        for number, line in enumerate(lines, 1):
            msg += str(number).rjust(3)
            prefix = "   " if line else ""
            if tb_top[1] == number:
                prefix = " > "
            msg += prefix + line + "\n"

    # Vim sends no WinLeave msg here.
    if hasattr(self, "_leaving_buffer"):
        self._leaving_buffer()  # pylint:disable=protected-access
    vim_helper.new_scratch_buffer(msg)


def wrap(func):
    """Decorator that will catch any Exception that 'func' throws and displays
    it in a new Vim scratch buffer."""

    @wraps(func)
    def wrapper(self, *args, **kwds):
        try:
            return func(self, *args, **kwds)
        except BdbQuit:
            pass  # A debugger stopped, but it's not really an error
        except PebkacError as e:
            if RemotePDB.is_enable():
                RemotePDB.pm()
            msg = "UltiSnips Error:\n\n"
            msg += str(e).strip()
            if RemotePDB.is_enable():
                host, port = RemotePDB.get_host_port()
                msg += "\nUltisnips' post mortem debug server caught the error. Run `telnet {}:{}` to inspect it with pdb\n".format(
                    host, port
                )
            _report_exception(self, msg, e)
        except Exception as e:  # pylint: disable=bare-except
            if RemotePDB.is_enable():
                RemotePDB.pm()
            msg = """An error occured. This is either a bug in UltiSnips or a bug in a
snippet definition. If you think this is a bug, please report it to
https://github.com/SirVer/ultisnips/issues/new
Please read and follow:
https://github.com/SirVer/ultisnips/blob/master/CONTRIBUTING.md#reproducing-bugs

Following is the full stack trace:
"""
            msg += traceback.format_exc()
            if RemotePDB.is_enable():
                host, port = RemotePDB.get_host_port()
                msg += "\nUltisnips' post mortem debug server caught the error. Run `telnet {}:{}` to inspect it with pdb\n".format(
                    host, port
                )

            _report_exception(self, msg, e)

    return wrapper
