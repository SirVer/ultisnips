#!/usr/bin/env python
# encoding: utf-8

"""Map/Unmap trigger keys."""

from UltiSnips import _vim

class KeyMapper(object):
    """See module doc."""

    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        self._expand_trigger = expand_trigger
        self._forward_trigger = forward_trigger
        self._backward_trigger = backward_trigger
        self._inner_mappings_in_place = False

    def map_inner_keys(self):
        """Map keys that should only be defined when a snippet is active."""
        if self._expand_trigger != self._forward_trigger:
            _vim.command("inoremap <buffer> <silent> " + self._forward_trigger +
                    " <C-R>=UltiSnips#JumpForwards()<cr>")
            _vim.command("snoremap <buffer> <silent> " + self._forward_trigger +
                    " <Esc>:call UltiSnips#JumpForwards()<cr>")
        _vim.command("inoremap <buffer> <silent> " + self._backward_trigger +
                " <C-R>=UltiSnips#JumpBackwards()<cr>")
        _vim.command("snoremap <buffer> <silent> " + self._backward_trigger +
                " <Esc>:call UltiSnips#JumpBackwards()<cr>")
        self._inner_mappings_in_place = True

    def unmap_inner_keys(self):
        """Unmap keys that should not be active when no snippet is active."""
        if not self._inner_mappings_in_place:
            return
        try:
            if self._expand_trigger != self._forward_trigger:
                _vim.command("iunmap <buffer> %s" % self._forward_trigger)
                _vim.command("sunmap <buffer> %s" % self._forward_trigger)
            _vim.command("iunmap <buffer> %s" % self._backward_trigger)
            _vim.command("sunmap <buffer> %s" % self._backward_trigger)
            self._inner_mappings_in_place = False
        except _vim.error:
            # This happens when a preview window was opened. This issues
            # CursorMoved, but not BufLeave. We have no way to unmap, until we
            # are back in our buffer
            pass
