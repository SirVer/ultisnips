#!/usr/bin/env python
# encoding: utf-8

"""Contains the SnippetManager facade used by all Vim Functions."""

from collections import defaultdict
from functools import wraps
import os
import traceback

from UltiSnips._diff import diff, guess_edit
from UltiSnips.compatibility import as_unicode
from UltiSnips.position import Position
from UltiSnips.providers import UltiSnipsFileProvider, \
        base_snippet_files_for, AddedSnippetsProvider
from UltiSnips.snippet_definition import SnippetDefinition
from UltiSnips.vim_state import VimState, VisualContentPreserver
import UltiSnips._vim as _vim

def _ask_snippets(snippets):
    """ Given a list of snippets, ask the user which one they
    want to use, and return it.
    """
    display = [as_unicode("%i: %s") % (i+1, s.description) for
            i, s in enumerate(snippets)]
    try:
        rv = _vim.eval("inputlist(%s)" % _vim.escape(display))
        if rv is None or rv == '0':
            return None
        rv = int(rv)
        if rv > len(snippets):
            rv = len(snippets)
        return snippets[rv-1]
    except _vim.error:
        # Likely "invalid expression", but might be translated. We have no way
        # of knowing the exact error, therefore, we ignore all errors silently.
        return None
    except KeyboardInterrupt:
        return None


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
            self._leaving_buffer()  # pylint:disable=protected-access
            _vim.new_scratch_buffer(msg)
    return wrapper


# TODO(sirver): This class is still too long. It should only contain public
# facing methods, most of the private methods should be moved outside of it.
class SnippetManager(object):
    """The main entry point for all UltiSnips functionality. All Vim functions
    call methods in this class."""

    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        self.expand_trigger = expand_trigger
        self.forward_trigger = forward_trigger
        self.backward_trigger = backward_trigger
        self._supertab_keys = None
        self._csnippets = []
        self._reset()

    @err_to_scratch_buffer
    def jump_forwards(self):
        """Jumps to the next tabstop."""
        _vim.command("let g:ulti_jump_forwards_res = 1")
        if not self._jump():
            _vim.command("let g:ulti_jump_forwards_res = 0")
            return self._handle_failure(self.forward_trigger)

    @err_to_scratch_buffer
    def jump_backwards(self):
        """Jumps to the previous tabstop."""
        _vim.command("let g:ulti_jump_backwards_res = 1")
        if not self._jump(True):
            _vim.command("let g:ulti_jump_backwards_res = 0")
            return self._handle_failure(self.backward_trigger)

    @err_to_scratch_buffer
    def expand(self):
        """Try to expand a snippet at the current position."""
        _vim.command("let g:ulti_expand_res = 1")
        if not self._try_expand():
            _vim.command("let g:ulti_expand_res = 0")
            self._handle_failure(self.expand_trigger)

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
            rv = self._jump()
        if not rv:
            _vim.command('let g:ulti_expand_or_jump_res = 0')
            self._handle_failure(self.expand_trigger)

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

        if len(snippets) == 0:
            self._handle_failure(self.backward_trigger)
            return True

        # Sort snippets alphabetically
        snippets.sort(key=lambda x: x.trigger)

        if not snippets:
            return True

        snippet = _ask_snippets(snippets)
        if not snippet:
            return True

        self._do_snippet(snippet, before)

        return True

    @err_to_scratch_buffer
    def add_snippet(self, trigger, value, description,
                    options, ft="all", globals=None):
        """Add a snippet to the list of known snippets of the given 'ft'."""
        self._added_snippets_provider.add_snippet(ft, SnippetDefinition(
            trigger, value, description, options, globals or {})
        )

    @err_to_scratch_buffer
    def expand_anon(self, value, trigger="", description="",
                    options="", globals=None):
        """Expand an anonymous snippet right here."""
        if globals is None:
            globals = {}

        before = _vim.buf.line_till_cursor
        snip = SnippetDefinition(trigger, value, description, options, globals)

        if not trigger or snip.matches(before):
            self._do_snippet(snip, before)
            return True
        else:
            return False

    def reset_buffer_filetypes(self):
        """Reset the filetypes for the current buffer."""
        if _vim.buf.number in self._filetypes:
            del self._filetypes[_vim.buf.number]

    def add_buffer_filetypes(self, ft):
        """Checks for changes in the list of snippet files or the contents of
        the snippet files and reloads them if necessary. """
        buf_fts = self._filetypes[_vim.buf.number]
        idx = -1
        for ft in ft.split("."):
            ft = ft.strip()
            if not ft:
                continue
            try:
                idx = buf_fts.index(ft)
            except ValueError:
                self._filetypes[_vim.buf.number].insert(idx + 1, ft)
                idx += 1

    @err_to_scratch_buffer
    def _cursor_moved(self):
        """Called whenever the cursor moved."""
        self._vstate.remember_position()
        if _vim.eval("mode()") not in 'in':
            return

        if self._ignore_movements:
            self._ignore_movements = False
            return

        if self._csnippets:
            cstart = self._csnippets[0].start.line
            cend = self._csnippets[0].end.line + \
                   self._vstate.diff_in_buffer_length
            ct = _vim.buf[cstart:cend + 1]
            lt = self._vstate.remembered_buffer
            pos = _vim.buf.cursor

            lt_span = [0, len(lt)]
            ct_span = [0, len(ct)]
            initial_line = cstart

            # Cut down on lines searched for changes. Start from behind and
            # remove all equal lines. Then do the same from the front.
            if lt and ct:
                while (lt[lt_span[1]-1] == ct[ct_span[1]-1] and
                        self._vstate.ppos.line < initial_line + lt_span[1]-1 and
                        pos.line < initial_line + ct_span[1]-1 and
                        (lt_span[0] < lt_span[1]) and
                        (ct_span[0] < ct_span[1])):
                    ct_span[1] -= 1
                    lt_span[1] -= 1
                while (lt_span[0] < lt_span[1] and
                       ct_span[0] < ct_span[1] and
                       lt[lt_span[0]] == ct[ct_span[0]] and
                       self._vstate.ppos.line >= initial_line and
                       pos.line >= initial_line):
                    ct_span[0] += 1
                    lt_span[0] += 1
                    initial_line += 1
            ct_span[0] = max(0, ct_span[0] - 1)
            lt_span[0] = max(0, lt_span[0] - 1)
            initial_line = max(cstart, initial_line - 1)

            lt = lt[lt_span[0]:lt_span[1]]
            ct = ct[ct_span[0]:ct_span[1]]

            try:
                rv, es = guess_edit(initial_line, lt, ct, self._vstate)
                if not rv:
                    lt = '\n'.join(lt)
                    ct = '\n'.join(ct)
                    es = diff(lt, ct, initial_line)
                self._csnippets[0].replay_user_edits(es)
            except IndexError:
                # Rather do nothing than throwing an error. It will be correct
                # most of the time
                pass

        self._check_if_still_inside_snippet()
        if self._csnippets:
            self._csnippets[0].update_textobjects()
            self._vstate.remember_buffer(self._csnippets[0])

    @err_to_scratch_buffer
    def _reset(self):
        """Reset the class to the state it had directly after creation."""
        self._vstate = VimState()
        self._filetypes = defaultdict(lambda: ['all'])
        self._visual_content = VisualContentPreserver()
        self._snippet_providers = [
            AddedSnippetsProvider(),
            UltiSnipsFileProvider()
        ]
        self._added_snippets_provider = self._snippet_providers[0]

        while len(self._csnippets):
            self._current_snippet_is_done()

        self._reinit()

    @err_to_scratch_buffer
    def _save_last_visual_selection(self):
        """
        This is called when the expand trigger is pressed in visual mode.
        Our job is to remember everything between '< and '> and pass it on to
        ${VISUAL} in case it will be needed.
        """
        self._visual_content.conserve()


    def _leaving_buffer(self):
        """Called when the user switches tabs/windows/buffers. It basically
        means that all snippets must be properly terminated."""
        while len(self._csnippets):
            self._current_snippet_is_done()
        self._reinit()

    def _reinit(self):
        """Resets transient state."""
        self._ctab = None
        self._ignore_movements = False

    def _check_if_still_inside_snippet(self):
        """Checks if the cursor is outside of the current snippet."""
        if self._cs and (
            not self._cs.start <= _vim.buf.cursor <= self._cs.end
        ):
            self._current_snippet_is_done()
            self._reinit()
            self._check_if_still_inside_snippet()

    def _current_snippet_is_done(self):
        """The current snippet should be terminated."""
        self._csnippets.pop()
        if not self._csnippets:
            _vim.command("call UltiSnips#map_keys#RestoreInnerKeys()")

    def _jump(self, backwards=False):
        """Helper method that does the actual jump."""
        jumped = False
        if self._cs:
            self._ctab = self._cs.select_next_tab(backwards)
            if self._ctab:
                if self._cs.snippet.has_option("s"):
                    lineno = _vim.buf.cursor.line
                    _vim.buf[lineno] = _vim.buf[lineno].rstrip()
                _vim.select(self._ctab.start, self._ctab.end)
                jumped = True
                if self._ctab.number == 0:
                    self._current_snippet_is_done()
            else:
                # This really shouldn't happen, because a snippet should
                # have been popped when its final tabstop was used.
                # Cleanup by removing current snippet and recursing.
                self._current_snippet_is_done()
                jumped = self._jump(backwards)
        if jumped:
            self._vstate.remember_position()
            self._vstate.remember_unnamed_register(self._ctab.current_text)
            self._ignore_movements = True
        return jumped

    def _leaving_insert_mode(self):
        """Called whenever we leave the insert mode."""
        self._vstate.restore_unnamed_register()

    def _handle_failure(self, trigger):
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

    def _snips(self, before, possible):
        """ Returns all the snippets for the given text
        before the cursor. If possible is True, then get all
        possible matches.
        """
        filetypes = self._filetypes[_vim.buf.number][::-1]
        snippets = []
        for provider in self._snippet_providers:
            snippets.extend(provider.get_snippets(filetypes, before, possible))
        return snippets

    def _do_snippet(self, snippet, before):
        """Expands the given snippet, and handles everything
        that needs to be done with it."""
        _vim.command("call UltiSnips#map_keys#MapInnerKeys()")

        # Adjust before, maybe the trigger is not the complete word
        text_before = before
        if snippet.matched:
            text_before = before[:-len(snippet.matched)]

        if self._cs:
            start = Position(_vim.buf.cursor.line, len(text_before))
            end = Position(_vim.buf.cursor.line, len(before))

            # It could be that our trigger contains the content of TextObjects
            # in our containing snippet. If this is indeed the case, we have to
            # make sure that those are properly killed. We do this by
            # pretending that the user deleted and retyped the text that our
            # trigger matched.
            edit_actions = [
                ("D", start.line, start.col, snippet.matched),
                ("I", start.line, start.col, snippet.matched),
            ]
            self._csnippets[0].replay_user_edits(edit_actions)

            si = snippet.launch(text_before, self._visual_content,
                    self._cs.find_parent_for_new_to(start), start, end)
        else:
            start = Position(_vim.buf.cursor.line, len(text_before))
            end = Position(_vim.buf.cursor.line, len(before))
            si = snippet.launch(text_before, self._visual_content,
                                None, start, end)

        self._visual_content.reset()
        self._csnippets.append(si)

        self._ignore_movements = True
        self._vstate.remember_buffer(self._csnippets[0])

        self._jump()

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
        self._do_snippet(snippet, before)
        return True

    @property
    def _cs(self):
        """The current snippet or None."""
        if not len(self._csnippets):
            return None
        return self._csnippets[-1]


    @property
    def _primary_filetype(self):
        """This filetype will be edited when UltiSnipsEdit is called without
        any arguments."""
        return self._filetypes[_vim.buf.number][0]

    # TODO(sirver): this should talk directly to the UltiSnipsFileProvider.
    def _file_to_edit(self, ft):  # pylint: disable=no-self-use
        """ Gets a file to edit based on the given filetype.
        If no filetype is given, uses the current filetype from Vim.

        Checks 'g:UltiSnipsSnippetsDir' and uses it if it exists
        If a non-shipped file already exists, it uses it.
        Otherwise uses a file in ~/.vim/ or ~/vimfiles
        """
        # This method is not using self, but is called by UltiSnips.vim and is
        # therefore in this class because it is the facade to Vim.
        edit = None
        existing = base_snippet_files_for(ft, False)
        filename = ft + ".snippets"

        if _vim.eval("exists('g:UltiSnipsSnippetsDir')") == "1":
            snipdir = _vim.eval("g:UltiSnipsSnippetsDir")
            edit = os.path.join(snipdir, filename)
        elif existing:
            edit = existing[-1] # last sourced/highest priority
        else:
            home = _vim.eval("$HOME")
            rtp = [os.path.realpath(os.path.expanduser(p))
                    for p in _vim.eval("&rtp").split(",")]
            snippet_dirs = ["UltiSnips"] + \
                    _vim.eval("g:UltiSnipsSnippetDirectories")
            us = snippet_dirs[-1]

            path = os.path.join(home, ".vim", us)
            for dirname in [".vim", "vimfiles"]:
                pth = os.path.join(home, dirname)
                if pth in rtp:
                    path = os.path.join(pth, us)

            if not os.path.isdir(path):
                os.mkdir(path)

            edit = os.path.join(path, filename)
        return edit
