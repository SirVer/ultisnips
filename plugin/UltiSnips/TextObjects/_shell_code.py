#!/usr/bin/env python
# encoding: utf-8

import os
import stat
import tempfile

from ._base import NoneditableTextObject

class ShellCode(NoneditableTextObject):
    def __init__(self, parent, token):
        code = token.code.replace("\\`", "`")

        # Write the code to a temporary file
        handle, path = tempfile.mkstemp(text=True)
        os.write(handle, code.encode("utf-8"))
        os.close(handle)

        os.chmod(path, stat.S_IRWXU)

        # TODO: use subprocess.
        # TODO: should not run in the constructor
        # Interpolate the shell code. We try to stay as compatible with Python
        # 2.3, therefore, we do not use the subprocess module here
        output = os.popen(path, "r").read()
        if len(output) and output[-1] == '\n':
            output = output[:-1]
        if len(output) and output[-1] == '\r':
            output = output[:-1]

        os.unlink(path)

        token.initial_text = output
        NoneditableTextObject.__init__(self, parent, token)


