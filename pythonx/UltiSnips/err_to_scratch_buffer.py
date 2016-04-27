# coding=utf8

from functools import wraps
import traceback
import re
import sys

from UltiSnips import _vim

def wrap(func):
    """Decorator that will catch any Exception that 'func' throws and displays
    it in a new Vim scratch buffer."""
    @wraps(func)
    def wrapper(self, *args, **kwds):
        try:
            return func(self, *args, **kwds)
        except Exception as e:  # pylint: disable=bare-except
            msg = \
                """An error occured. This is either a bug in UltiSnips or a bug in a
snippet definition. If you think this is a bug, please report it to
https://github.com/SirVer/ultisnips/issues/new.

Following is the full stack trace:
"""

            msg += traceback.format_exc()
            if hasattr(e, 'snippet_info'):
                msg += "\nSnippet, caused error:\n"
                msg += re.sub(
                    '^(?=\S)', '  ', e.snippet_info, flags=re.MULTILINE
                )
            # snippet_code comes from _python_code.py, it's set manually for
            # providing error message with stacktrace of failed python code
            # inside of the snippet.
            if hasattr(e, 'snippet_code'):
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
            if hasattr(self, '_leaving_buffer'):
                self._leaving_buffer()  # pylint:disable=protected-access
            _vim.new_scratch_buffer(msg)
    return wrapper
