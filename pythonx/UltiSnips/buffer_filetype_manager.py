"""Keep the filetype information for each buffer."""

from collections import defaultdict

from UltiSnips import _vim

class BufferFileTypeManager(object):
    """See module doc."""

    def __init__(self):
        self._buffer_filetypes = defaultdict(lambda: ['all'])

    def reset(self):
        """Reset the filetypes for the current buffer."""
        if _vim.buf.number in self._buffer_filetypes:
            del self._buffer_filetypes[_vim.buf.number]

    def add(self, ft):
        """Checks for changes in the list of snippet files or the contents of
        the snippet files and reloads them if necessary. """
        buf_fts = self._buffer_filetypes[_vim.buf.number]
        idx = -1
        for ft in ft.split("."):
            ft = ft.strip()
            if not ft:
                continue
            try:
                idx = buf_fts.index(ft)
            except ValueError:
                self._buffer_filetypes[_vim.buf.number].insert(idx + 1, ft)
                idx += 1

    def get(self):
        """Get filetypes for current buffer."""
        return self._buffer_filetypes[_vim.buf.number]
