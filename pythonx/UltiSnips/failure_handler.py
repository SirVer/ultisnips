"""Handles failure in SnippetManager."""

from UltiSnips import _vim

class FailureHandler(object):
    """See module doc."""

    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        self._supertab_keys = None
        self._expand_trigger = expand_trigger
        self._forward_trigger = forward_trigger
        self._backward_trigger = backward_trigger

    def handle_expand(self):
        """Handles failure while triggered by expand."""
        self._handle(self._expand_trigger)

    def handle_forward(self):
        """Handles failure while triggered by forward jump."""
        self._handle(self._forward_trigger)

    def handle_backward(self):
        """Handles failure whil trigged by backward jump."""
        self._handle(self._backward_trigger)

    def _handle(self, trigger):
        """Mainly make sure that we play well with SuperTab."""
        if trigger.lower() == "<tab>":
            feedkey = "\\" + trigger
        elif trigger.lower() == "<s-tab>":
            feedkey = "\\" + trigger
        else:
            feedkey = None
        mode = "n"
        if not self._supertab_keys:
            if _vim.eval("exists('g:SuperTabMappingForward')") != "0":
                self._supertab_keys = (
                    _vim.eval("g:SuperTabMappingForward"),
                    _vim.eval("g:SuperTabMappingBackward"),
                )
            else:
                self._supertab_keys = ['', '']

        for idx, sttrig in enumerate(self._supertab_keys):
            if trigger.lower() == sttrig.lower():
                if idx == 0:
                    feedkey = r"\<Plug>SuperTabForward"
                    mode = "n"
                elif idx == 1:
                    feedkey = r"\<Plug>SuperTabBackward"
                    mode = "p"
                # Use remap mode so SuperTab mappings will be invoked.
                break

        if (feedkey == r"\<Plug>SuperTabForward" or
                feedkey == r"\<Plug>SuperTabBackward"):
            _vim.command("return SuperTab(%s)" % _vim.escape(mode))
        elif feedkey:
            _vim.command("return %s" % _vim.escape(feedkey))
