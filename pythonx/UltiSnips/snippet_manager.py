#!/usr/bin/env python
# encoding: utf-8

"""Contains the SnippetManager facade used by all Vim Functions."""

from functools import wraps
import os
import platform
import traceback

from UltiSnips import _vim
from UltiSnips.buffer_filetype_manager import BufferFileTypeManager
from UltiSnips.compatibility import as_unicode
from UltiSnips.failure_handler import FailureHandler
from UltiSnips.snippet.definition import UltiSnipsSnippetDefinition
from UltiSnips.snippet.source import UltiSnipsFileSource, SnipMateFileSource, \
        find_all_snippet_files, find_snippet_files, AddedSnippetsSource
from UltiSnips.snippet_performer import SnippetPerformer
from UltiSnips.text import escape

def _ask_user(a, formatted):
    """Asks the user using inputlist() and returns the selected element or
    None."""
    try:
        rv = _vim.eval("inputlist(%s)" % _vim.escape(formatted))
        if rv is None or rv == '0':
            return None
        rv = int(rv)
        if rv > len(a):
            rv = len(a)
        return a[rv-1]
    except _vim.error:
        # Likely "invalid expression", but might be translated. We have no way
        # of knowing the exact error, therefore, we ignore all errors silently.
        return None
    except KeyboardInterrupt:
        return None

def _ask_snippets(snippets):
    """ Given a list of snippets, ask the user which one they
    want to use, and return it.
    """
    display = [as_unicode("%i: %s (%s)") % (i+1, escape(s.description, '\\'),
        escape(s.location, '\\')) for i, s in enumerate(snippets)]
    return _ask_user(snippets, display)

def _snippet_dir():
    """Get the path of the snippet directory.
    """
    if _vim.eval("exists('g:UltiSnipsSnippetsDir')") == "1":
        return _vim.eval("g:UltiSnipsSnippetsDir")
    else:
        home_path = _vim.eval("$HOME")
        if platform.system() == "Windows":
            return os.path.join(home_path, "vimfiles", "UltiSnips")
        else:
            return os.path.join(home_path, ".vim", "UltiSnips")

def err_to_scratch_buffer(func):
    """Decorator that will catch any Exception that 'func' throws and displays
    it in a new Vim scratch buffer."""
    @wraps(func)
    def wrapper(self, *args, **kwds):
        try:
            return func(self, *args, **kwds)
        except: # pylint: disable=bare-except
            msg = \
"""An error occured. This is either a bug in UltiSnips or a bug in a
snippet definition. If you think this is a bug, please report it to
https://github.com/SirVer/ultisnips/issues/new.

Following is the full stack trace:
"""
            msg += traceback.format_exc()
            # Vim sends no WinLeave msg here.
            self.leaving_buffer()
            _vim.new_scratch_buffer(msg)
    return wrapper


# TODO(cwahbong): Most of the private methods are extracted.  Still need some
# works.
class SnippetManager(object):
    """The main entry point for all UltiSnips functionality. All Vim functions
    call methods in this class."""

    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        self._failure_handler = FailureHandler(
                expand_trigger, forward_trigger, backward_trigger)
        self._snippet_performer = SnippetPerformer(
                expand_trigger, forward_trigger, backward_trigger)
        self._buffer_filetype_manager = BufferFileTypeManager()

        sources = (
                ("ultisnips_files", UltiSnipsFileSource()),
                ("added", AddedSnippetsSource()),
                ("snipmate_files", SnipMateFileSource()),
        )
        for name, source in sources:
            self._snippet_performer.register(name, source)

    @err_to_scratch_buffer
    def jump_forwards(self):
        """Jumps to the next tabstop."""
        _vim.command("let g:ulti_jump_forwards_res = 1")
        if not self._snippet_performer.jump():
            _vim.command("let g:ulti_jump_forwards_res = 0")
            return self._failure_handler.handle_forward()

    @err_to_scratch_buffer
    def jump_backwards(self):
        """Jumps to the previous tabstop."""
        _vim.command("let g:ulti_jump_backwards_res = 1")
        if not self._snippet_performer.jump(True):
            _vim.command("let g:ulti_jump_backwards_res = 0")
            return self._failure_handler.handle_backward()

    def _try_expand(self):
        """Try to expand a snippet in the current place."""
        before = _vim.buf.line_till_cursor
        if not before:
            return False
        snippets = self._snips(before, False)
        if not snippets:
            # No snippet found
            return False
        elif len(snippets) == 1:
            snippet = snippets[0]
        else:
            snippet = _ask_snippets(snippets)
            if not snippet:
                return True
        self._snippet_performer.do_snippet(snippet, before)
        return True

    @err_to_scratch_buffer
    def expand(self):
        """Try to expand a snippet at the current position."""
        _vim.command("let g:ulti_expand_res = 1")
        if not self._try_expand():
            _vim.command("let g:ulti_expand_res = 0")
            self._failure_handler.handle_expand()

    @err_to_scratch_buffer
    def expand_or_jump(self):
        """
        This function is used for people who wants to have the same trigger for
        expansion and forward jumping. It first tries to expand a snippet, if
        this fails, it tries to jump forward.
        """
        _vim.command('let g:ulti_expand_or_jump_res = 1')
        rv = self._try_expand()
        if not rv:
            _vim.command('let g:ulti_expand_or_jump_res = 2')
            rv = self._snippet_performer.jump()
        if not rv:
            _vim.command('let g:ulti_expand_or_jump_res = 0')
            self._failure_handler.handle_expand()

    @err_to_scratch_buffer
    def snippets_in_current_scope(self):
        """Returns the snippets that could be expanded to Vim as a global
        variable."""
        before = _vim.buf.line_till_cursor
        snippets = self._snips(before, True)

        # Sort snippets alphabetically
        snippets.sort(key=lambda x: x.trigger)
        for snip in snippets:
            description = snip.description[snip.description.find(snip.trigger) +
                len(snip.trigger) + 2:]

            key = as_unicode(snip.trigger)
            description = as_unicode(description)

            # remove surrounding "" or '' in snippet description if it exists
            if len(description) > 2:
                if (description[0] == description[-1] and
                        description[0] in "'\""):
                    description = description[1:-1]

            _vim.command(as_unicode(
                "let g:current_ulti_dict['{key}'] = '{val}'").format(
                    key=key.replace("'", "''"),
                    val=description.replace("'", "''")))

    @err_to_scratch_buffer
    def list_snippets(self):
        """Shows the snippets that could be expanded to the User and let her
        select one."""
        before = _vim.buf.line_till_cursor
        snippets = self._snips(before, True)

        if not snippets:
            self._failure_handler.handle_backward()
            return

        snippets.sort(key=lambda x: x.trigger)
        snippet = _ask_snippets(snippets)
        if not snippet:
            return

        self._snippet_performer.do_snippet(snippet, before)
        return

    @err_to_scratch_buffer
    def add_snippet(self, trigger, value, description,
            options, ft="all", priority=0):
        """Add a snippet to the list of known snippets of the given 'ft'."""
        added_source = self._snippet_performer.get_source("added")
        added_source.add_snippet(ft,
                UltiSnipsSnippetDefinition(priority, trigger, value,
                    description, options, {}, "added"))

    @err_to_scratch_buffer
    def expand_anon(self, value, trigger="", description="", options=""):
        """Expand an anonymous snippet right here."""
        before = _vim.buf.line_till_cursor
        snip = UltiSnipsSnippetDefinition(0, trigger, value, description,
                options, {}, "")

        if not trigger or snip.matches(before):
            self._snippet_performer.do_snippet(snip, before)
            return True
        else:
            return False

    def register_snippet_source(self, name, snippet_source):
        """Facing method.  See SnippetSourceCollector.register() for
        detail."""
        self._snippet_performer.register(name, snippet_source)

    def unregister_snippet_source(self, name):
        """Facing method.  See SnippetSourceCollector.unregister() for
        detail."""
        self._snippet_performer.unregister(name)

    @err_to_scratch_buffer
    def filetype_changed(self):
        """Called when the filetype changed."""
        self._buffer_filetype_manager.reset()
        self._buffer_filetype_manager.add(_vim.eval("&ft"))

    @err_to_scratch_buffer
    def add_buffer_filetypes(self, ft):
        """Checks for changes in the list of snippet files or the contents of
        the snippet files and reloads them if necessary. """
        self._buffer_filetype_manager.add(ft)

    @err_to_scratch_buffer
    def cursor_moved(self):
        """Called whenever the cursor moved."""
        self._snippet_performer.cursor_moved()

    @err_to_scratch_buffer
    def save_last_visual_selection(self):
        """This is called when the expand trigger is pressed in visual mode.
        Our job is to remember everything between '< and '> and pass it on to
        ${VISUAL} in case it will be needed.
        """
        self._snippet_performer._visual_content.conserve() # XXX protected

    def leaving_buffer(self):
        """Called when the user switches tabs/windows/buffers. It basically
        means that all snippets must be properly terminated."""
        self._snippet_performer.leaving_buffer()

    def leaving_insert_mode(self):
        """Called whenever we leave the insert mode."""
        # XXX protected
        self._snippet_performer._vstate.restore_unnamed_register()

    def _snips(self, before, partial):
        """Returns all the snippets for the given text before the cursor. If
        partial is True, then get also return partial matches. """
        filetypes = self._buffer_filetype_manager.get()
        return self._snippet_performer.snips(filetypes, before, partial)

    def _potential_files_to_edit(self, requested_ft, bang):
        """Get all files that may be edited when invoking UltiSnipsEdit
        in vim.
        """
        potentials = set()
        snippet_dir = _snippet_dir()

        filetypes = []
        if requested_ft:
            filetypes.append(requested_ft)
        else:
            if bang:
                filetypes.extend(self._buffer_filetype_manager.get())
            else:
                filetypes.append(self._buffer_filetype_manager.get()[0])

        for ft in filetypes:
            potentials.update(find_snippet_files(ft, snippet_dir))
            potentials.add(os.path.join(snippet_dir,
                ft + '.snippets'))
            if bang:
                potentials.update(find_all_snippet_files(ft))

        return set(os.path.realpath(os.path.expanduser(p)) for p in potentials)

    def file_to_edit(self, requested_ft, bang):
        """Returns a file to be edited for the given requested_ft. If 'bang' is
        empty only private files in g:UltiSnipsSnippetsDir are considered,
        otherwise all files are considered and the user gets to choose.
        """
        potentials = self._potential_files_to_edit(requested_ft, bang)

        if len(potentials) > 1:
            files = sorted(potentials)
            formatted = [as_unicode('%i: %s') % (i, escape(fn, '\\')) for
                    i, fn in enumerate(files, 1)]
            file_to_edit = _ask_user(files, formatted)
            if file_to_edit is None:
                return ""
        else:
            file_to_edit = potentials.pop()

        dirname = os.path.dirname(file_to_edit)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        return file_to_edit
