#!/usr/bin/env python
# encoding: utf-8

import os
import subprocess
import stat
import tempfile

from UltiSnips.compatibility import as_unicode
from UltiSnips.text_objects._base import NoneditableTextObject

class ShellCode(NoneditableTextObject):
    def __init__(self, parent, token):
        NoneditableTextObject.__init__(self, parent, token)

        self._code = token.code.replace("\\`", "`")

    def _update(self, done, not_done):
        # Write the code to a temporary file
        handle, path = tempfile.mkstemp(text=True)
        os.write(handle, self._code.encode("utf-8"))
        os.close(handle)
        os.chmod(path, stat.S_IRWXU)

        # Execute the file and read stdout
        proc = subprocess.Popen(path, shell=True, stdout=subprocess.PIPE)
        proc.wait()
        output = as_unicode(proc.stdout.read())

        if len(output) and output[-1] == '\n':
            output = output[:-1]
        if len(output) and output[-1] == '\r':
            output = output[:-1]

        os.unlink(path)

        self.overwrite(output)
        self._parent._del_child(self)

        return True


