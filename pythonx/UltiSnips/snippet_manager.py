#!/usr/bin/env python
# encoding: utf-8

"""Contains the SnippetManager facade used by all Vim Functions."""

from collections import defaultdict
from contextlib import contextmanager
import os
import platform
import sys
import vim

from UltiSnips import vim_helper
from UltiSnips import err_to_scratch_buffer
from UltiSnips.diff import diff, guess_edit
from UltiSnips.compatibility import as_unicode
from UltiSnips.position import Position
from UltiSnips.snippet.definition import UltiSnipsSnippetDefinition
from UltiSnips.snippet.source import (
    UltiSnipsFileSource,
    SnipMateFileSource,
    find_all_snippet_files,
    find_snippet_files,
    AddedSnippetsSource,
)
from UltiSnips.text import escape
from UltiSnips.vim_state import VimState, VisualContentPreserver
from UltiSnips.buffer_proxy import use_proxy_buffer, suspend_proxy_edits


def _ask_user(a, formatted):
    """Asks the user using inputlist() and returns the selected element or
    None."""
    try:
        rv = vim_helper.eval("inputlist(%s)" % vim_helper.escape(formatted))
        if rv is None or rv == "0":
            return None
        rv = int(rv)
        if rv > len(a):
            rv = len(a)
        return a[rv - 1]
    except vim_helper.error:
        # Likely "invalid expression", but might be translated. We have no way
        # of knowing the exact error, therefore, we ignore all errors silently.
        return None
    except KeyboardInterrupt:
        return None


def _ask_snippets(snippets):
    """Given a list of snippets, ask the user which one they want to use, and
    return it."""
    display = [
        as_unicode("%i: %s (%s)")
        % (i + 1, escape(s.description, "\\"), escape(s.location, "\\"))
        for i, s in enumerate(snippets)
    ]
    return _ask_user(snippets, display)


# TODO(sirver): This class is still too long. It should only contain public
# facing methods, most of the private methods should be moved outside of it.
class SnippetManager(object):

    """The main entry point for all UltiSnips functionality.

    All Vim functions call methods in this class.

    """

    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        self.expand_trigger = expand_trigger
        self.forward_trigger = forward_trigger
        self.backward_trigger = backward_trigger
        self._inner_state_up = False
        self._supertab_keys = None

        self._active_snippets = []
        self._added_buffer_filetypes = defaultdict(lambda: [])

        self._vstate = VimState()
        self._visual_content = VisualContentPreserver()

        self._snippet_sources = []

        self._snip_expanded_in_action = False
        self._inside_action = False

        self._last_change = ("", Position(-1, -1))

        self._added_snippets_source = AddedSnippetsSource()
        self.register_snippet_source("ultisnips_files", UltiSnipsFileSource())
        self.register_snippet_source("added", self._added_snippets_source)

        enable_snipmate = "1"
        if vim_helper.eval("exists('g:UltiSnipsEnableSnipMate')") == "1":
            enable_snipmate = vim_helper.eval("g:UltiSnipsEnableSnipMate")
        if enable_snipmate == "1":
            self.register_snippet_source("snipmate_files", SnipMateFileSource())

        self._should_update_textobjects = False
        self._should_reset_visual = False

        self._reinit()

    @err_to_scratch_buffer.wrap
    def jump_forwards(self):
        """Jumps to the next tabstop."""
        vim_helper.command("let g:ulti_jump_forwards_res = 1")
        vim_helper.command("let &undolevels = &undolevels")
        if not self._jump():
            vim_helper.command("let g:ulti_jump_forwards_res = 0")
            return self._handle_failure(self.forward_trigger)
        return None

    @err_to_scratch_buffer.wrap
    def jump_backwards(self):
        """Jumps to the previous tabstop."""
        vim_helper.command("let g:ulti_jump_backwards_res = 1")
        vim_helper.command("let &undolevels = &undolevels")
        if not self._jump(True):
            vim_helper.command("let g:ulti_jump_backwards_res = 0")
            return self._handle_failure(self.backward_trigger)
        return None

    @err_to_scratch_buffer.wrap
    def expand(self):
        """Try to expand a snippet at the current position."""
        vim_helper.command("let g:ulti_expand_res = 1")
        if not self._try_expand():
            vim_helper.command("let g:ulti_expand_res = 0")
            self._handle_failure(self.expand_trigger)

    @err_to_scratch_buffer.wrap
    def expand_or_jump(self):
        """This function is used for people who wants to have the same trigger
        for expansion and forward jumping.

        It first tries to expand a snippet, if this fails, it tries to
        jump forward.

        """
        vim_helper.command("let g:ulti_expand_or_jump_res = 1")
        rv = self._try_expand()
        if not rv:
            vim_helper.command("let g:ulti_expand_or_jump_res = 2")
            rv = self._jump()
        if not rv:
            vim_helper.command("let g:ulti_expand_or_jump_res = 0")
            self._handle_failure(self.expand_trigger)

    @err_to_scratch_buffer.wrap
    def snippets_in_current_scope(self, search_all):
        """Returns the snippets that could be expanded to Vim as a global
        variable."""
        before = "" if search_all else vim_helper.buf.line_till_cursor
        snippets = self._snips(before, True)

        # Sort snippets alphabetically
        snippets.sort(key=lambda x: x.trigger)
        for snip in snippets:
            description = snip.description[
                snip.description.find(snip.trigger) + len(snip.trigger) + 2 :
            ]

            location = snip.location if snip.location else ""

            key = as_unicode(snip.trigger)
            description = as_unicode(description)

            # remove surrounding "" or '' in snippet description if it exists
            if len(description) > 2:
                if description[0] == description[-1] and description[0] in "'\"":
                    description = description[1:-1]

            vim_helper.command(
                as_unicode("let g:current_ulti_dict['{key}'] = '{val}'").format(
                    key=key.replace("'", "''"), val=description.replace("'", "''")
                )
            )

            if search_all:
                vim_helper.command(
                    as_unicode(
                        (
                            "let g:current_ulti_dict_info['{key}'] = {{"
                            "'description': '{description}',"
                            "'location': '{location}',"
                            "}}"
                        )
                    ).format(
                        key=key.replace("'", "''"),
                        location=location.replace("'", "''"),
                        description=description.replace("'", "''"),
                    )
                )

    @err_to_scratch_buffer.wrap
    def list_snippets(self):
        """Shows the snippets that could be expanded to the User and let her
        select one."""
        before = vim_helper.buf.line_till_cursor
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

    @err_to_scratch_buffer.wrap
    def add_snippet(
        self,
        trigger,
        value,
        description,
        options,
        ft="all",
        priority=0,
        context=None,
        actions=None,
    ):
        """Add a snippet to the list of known snippets of the given 'ft'."""
        self._added_snippets_source.add_snippet(
            ft,
            UltiSnipsSnippetDefinition(
                priority,
                trigger,
                value,
                description,
                options,
                {},
                "added",
                context,
                actions,
            ),
        )

    @err_to_scratch_buffer.wrap
    def expand_anon(
        self, value, trigger="", description="", options="", context=None, actions=None
    ):
        """Expand an anonymous snippet right here."""
        before = vim_helper.buf.line_till_cursor
        snip = UltiSnipsSnippetDefinition(
            0, trigger, value, description, options, {}, "", context, actions
        )

        if not trigger or snip.matches(before, self._visual_content):
            self._do_snippet(snip, before)
            return True
        return False

    def register_snippet_source(self, name, snippet_source):
        """Registers a new 'snippet_source' with the given 'name'.

        The given class must be an instance of SnippetSource. This
        source will be queried for snippets.

        """
        self._snippet_sources.append((name, snippet_source))

    def unregister_snippet_source(self, name):
        """Unregister the source with the given 'name'.

        Does nothing if it is not registered.

        """
        for index, (source_name, _) in enumerate(self._snippet_sources):
            if name == source_name:
                self._snippet_sources = (
                    self._snippet_sources[:index] + self._snippet_sources[index + 1 :]
                )
                break

    def get_buffer_filetypes(self):
        return (
            self._added_buffer_filetypes[vim_helper.buf.number]
            + vim_helper.buf.filetypes
            + ["all"]
        )

    def add_buffer_filetypes(self, filetypes):
        buf_fts = self._added_buffer_filetypes[vim_helper.buf.number]
        idx = -1
        for ft in filetypes.split("."):
            ft = ft.strip()
            if not ft:
                continue
            try:
                idx = buf_fts.index(ft)
            except ValueError:
                self._added_buffer_filetypes[vim_helper.buf.number].insert(idx + 1, ft)
                idx += 1

    @err_to_scratch_buffer.wrap
    def _cursor_moved(self):
        """Called whenever the cursor moved."""
        self._should_update_textobjects = False

        self._vstate.remember_position()
        if vim_helper.eval("mode()") not in "in":
            return

        if self._ignore_movements:
            self._ignore_movements = False
            return

        if self._active_snippets:
            cstart = self._active_snippets[0].start.line
            cend = (
                self._active_snippets[0].end.line + self._vstate.diff_in_buffer_length
            )
            ct = vim_helper.buf[cstart : cend + 1]
            lt = self._vstate.remembered_buffer
            pos = vim_helper.buf.cursor

            lt_span = [0, len(lt)]
            ct_span = [0, len(ct)]
            initial_line = cstart

            # Cut down on lines searched for changes. Start from behind and
            # remove all equal lines. Then do the same from the front.
            if lt and ct:
                while (
                    lt[lt_span[1] - 1] == ct[ct_span[1] - 1]
                    and self._vstate.ppos.line < initial_line + lt_span[1] - 1
                    and pos.line < initial_line + ct_span[1] - 1
                    and (lt_span[0] < lt_span[1])
                    and (ct_span[0] < ct_span[1])
                ):
                    ct_span[1] -= 1
                    lt_span[1] -= 1
                while (
                    lt_span[0] < lt_span[1]
                    and ct_span[0] < ct_span[1]
                    and lt[lt_span[0]] == ct[ct_span[0]]
                    and self._vstate.ppos.line >= initial_line
                    and pos.line >= initial_line
                ):
                    ct_span[0] += 1
                    lt_span[0] += 1
                    initial_line += 1
            ct_span[0] = max(0, ct_span[0] - 1)
            lt_span[0] = max(0, lt_span[0] - 1)
            initial_line = max(cstart, initial_line - 1)

            lt = lt[lt_span[0] : lt_span[1]]
            ct = ct[ct_span[0] : ct_span[1]]

            try:
                rv, es = guess_edit(initial_line, lt, ct, self._vstate)
                if not rv:
                    lt = "\n".join(lt)
                    ct = "\n".join(ct)
                    es = diff(lt, ct, initial_line)
                self._active_snippets[0].replay_user_edits(es, self._ctab)
            except IndexError:
                # Rather do nothing than throwing an error. It will be correct
                # most of the time
                pass

        self._check_if_still_inside_snippet()
        if self._active_snippets:
            self._active_snippets[0].update_textobjects(vim_helper.buf)
            self._vstate.remember_buffer(self._active_snippets[0])

    def _setup_inner_state(self):
        """Map keys and create autocommands that should only be defined when a
        snippet is active."""
        if self._inner_state_up:
            return
        if self.expand_trigger != self.forward_trigger:
            vim_helper.command(
                "inoremap <buffer><nowait><silent> "
                + self.forward_trigger
                + " <C-R>=UltiSnips#JumpForwards()<cr>"
            )
            vim_helper.command(
                "snoremap <buffer><nowait><silent> "
                + self.forward_trigger
                + " <Esc>:call UltiSnips#JumpForwards()<cr>"
            )
        vim_helper.command(
            "inoremap <buffer><nowait><silent> "
            + self.backward_trigger
            + " <C-R>=UltiSnips#JumpBackwards()<cr>"
        )
        vim_helper.command(
            "snoremap <buffer><nowait><silent> "
            + self.backward_trigger
            + " <Esc>:call UltiSnips#JumpBackwards()<cr>"
        )

        # Setup the autogroups.
        vim_helper.command("augroup UltiSnips")
        vim_helper.command("autocmd!")
        vim_helper.command("autocmd CursorMovedI * call UltiSnips#CursorMoved()")
        vim_helper.command("autocmd CursorMoved * call UltiSnips#CursorMoved()")

        vim_helper.command("autocmd InsertLeave * call UltiSnips#LeavingInsertMode()")

        vim_helper.command("autocmd BufEnter * call UltiSnips#LeavingBuffer()")
        vim_helper.command("autocmd CmdwinEnter * call UltiSnips#LeavingBuffer()")
        vim_helper.command("autocmd CmdwinLeave * call UltiSnips#LeavingBuffer()")

        # Also exit the snippet when we enter a unite complete buffer.
        vim_helper.command("autocmd Filetype unite call UltiSnips#LeavingBuffer()")

        vim_helper.command("augroup END")

        vim_helper.command(
            "silent doautocmd <nomodeline> User UltiSnipsEnterFirstSnippet"
        )
        self._inner_state_up = True

    def _teardown_inner_state(self):
        """Reverse _setup_inner_state."""
        if not self._inner_state_up:
            return
        try:
            vim_helper.command(
                "silent doautocmd <nomodeline> User UltiSnipsExitLastSnippet"
            )
            if self.expand_trigger != self.forward_trigger:
                vim_helper.command("iunmap <buffer> %s" % self.forward_trigger)
                vim_helper.command("sunmap <buffer> %s" % self.forward_trigger)
            vim_helper.command("iunmap <buffer> %s" % self.backward_trigger)
            vim_helper.command("sunmap <buffer> %s" % self.backward_trigger)
            vim_helper.command("augroup UltiSnips")
            vim_helper.command("autocmd!")
            vim_helper.command("augroup END")
            self._inner_state_up = False
        except vim_helper.error:
            # This happens when a preview window was opened. This issues
            # CursorMoved, but not BufLeave. We have no way to unmap, until we
            # are back in our buffer
            pass

    @err_to_scratch_buffer.wrap
    def _save_last_visual_selection(self):
        """This is called when the expand trigger is pressed in visual mode.
        Our job is to remember everything between '< and '> and pass it on to.

        ${VISUAL} in case it will be needed.

        """
        self._visual_content.conserve()

    def _leaving_buffer(self):
        """Called when the user switches tabs/windows/buffers.

        It basically means that all snippets must be properly
        terminated.

        """
        while self._active_snippets:
            self._current_snippet_is_done()
        self._reinit()

    def _reinit(self):
        """Resets transient state."""
        self._ctab = None
        self._ignore_movements = False

    def _check_if_still_inside_snippet(self):
        """Checks if the cursor is outside of the current snippet."""
        if self._current_snippet and (
            not self._current_snippet.start
            <= vim_helper.buf.cursor
            <= self._current_snippet.end
        ):
            self._current_snippet_is_done()
            self._reinit()
            self._check_if_still_inside_snippet()

    def _current_snippet_is_done(self):
        """The current snippet should be terminated."""
        self._active_snippets.pop()
        if not self._active_snippets:
            self._teardown_inner_state()

    def _jump(self, backwards=False):
        """Helper method that does the actual jump."""
        if self._should_update_textobjects:
            self._should_reset_visual = False
            self._cursor_moved()

        # we need to set 'onemore' there, because of limitations of the vim
        # API regarding cursor movements; without that test
        # 'CanExpandAnonSnippetInJumpActionWhileSelected' will fail
        with vim_helper.option_set_to("ve", "onemore"):
            jumped = False

            # We need to remember current snippets stack here because of
            # post-jump action on the last tabstop should be able to access
            # snippet instance which is ended just now.
            stack_for_post_jump = self._active_snippets[:]

            # If next tab has length 1 and the distance between itself and
            # self._ctab is 1 then there is 1 less CursorMove events.  We
            # cannot ignore next movement in such case.
            ntab_short_and_near = False

            if self._current_snippet:
                snippet_for_action = self._current_snippet
            elif stack_for_post_jump:
                snippet_for_action = stack_for_post_jump[-1]
            else:
                snippet_for_action = None

            if self._current_snippet:
                ntab = self._current_snippet.select_next_tab(backwards)
                if ntab:
                    if self._current_snippet.snippet.has_option("s"):
                        lineno = vim_helper.buf.cursor.line
                        vim_helper.buf[lineno] = vim_helper.buf[lineno].rstrip()
                    vim_helper.select(ntab.start, ntab.end)
                    jumped = True
                    if (
                        self._ctab is not None
                        and ntab.start - self._ctab.end == Position(0, 1)
                        and ntab.end - ntab.start == Position(0, 1)
                    ):
                        ntab_short_and_near = True

                    self._ctab = ntab

                    # Run interpolations again to update new placeholder
                    # values, binded to currently newly jumped placeholder.
                    self._visual_content.conserve_placeholder(self._ctab)
                    self._current_snippet.current_placeholder = (
                        self._visual_content.placeholder
                    )
                    self._should_reset_visual = False
                    self._active_snippets[0].update_textobjects(vim_helper.buf)
                    # Open any folds this might have created
                    vim_helper.command("normal! zv")
                    self._vstate.remember_buffer(self._active_snippets[0])

                    if ntab.number == 0 and self._active_snippets:
                        self._current_snippet_is_done()
                else:
                    # This really shouldn't happen, because a snippet should
                    # have been popped when its final tabstop was used.
                    # Cleanup by removing current snippet and recursing.
                    self._current_snippet_is_done()
                    jumped = self._jump(backwards)

            if jumped:
                if self._ctab:
                    self._vstate.remember_position()
                    self._vstate.remember_unnamed_register(self._ctab.current_text)
                if not ntab_short_and_near:
                    self._ignore_movements = True

            if len(stack_for_post_jump) > 0 and ntab is not None:
                with use_proxy_buffer(stack_for_post_jump, self._vstate):
                    snippet_for_action.snippet.do_post_jump(
                        ntab.number,
                        -1 if backwards else 1,
                        stack_for_post_jump,
                        snippet_for_action,
                    )

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
            if vim_helper.eval("exists('g:SuperTabMappingForward')") != "0":
                self._supertab_keys = (
                    vim_helper.eval("g:SuperTabMappingForward"),
                    vim_helper.eval("g:SuperTabMappingBackward"),
                )
            else:
                self._supertab_keys = ["", ""]

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

        if feedkey in (r"\<Plug>SuperTabForward", r"\<Plug>SuperTabBackward"):
            vim_helper.command("return SuperTab(%s)" % vim_helper.escape(mode))
        elif feedkey:
            vim_helper.command("return %s" % vim_helper.escape(feedkey))

    def _snips(self, before, partial, autotrigger_only=False):
        """Returns all the snippets for the given text before the cursor.

        If partial is True, then get also return partial matches.

        """
        filetypes = self.get_buffer_filetypes()[::-1]
        matching_snippets = defaultdict(list)
        clear_priority = None
        cleared = {}
        for _, source in self._snippet_sources:
            source.ensure(filetypes)

        # Collect cleared information from sources.
        for _, source in self._snippet_sources:
            sclear_priority = source.get_clear_priority(filetypes)
            if sclear_priority is not None and (
                clear_priority is None or sclear_priority > clear_priority
            ):
                clear_priority = sclear_priority
            for key, value in source.get_cleared(filetypes).items():
                if key not in cleared or value > cleared[key]:
                    cleared[key] = value

        for _, source in self._snippet_sources:
            possible_snippets = source.get_snippets(
                filetypes, before, partial, autotrigger_only, self._visual_content
            )

            for snippet in possible_snippets:
                if (clear_priority is None or snippet.priority > clear_priority) and (
                    snippet.trigger not in cleared
                    or snippet.priority > cleared[snippet.trigger]
                ):
                    matching_snippets[snippet.trigger].append(snippet)
        if not matching_snippets:
            return []

        # Now filter duplicates and only keep the one with the highest
        # priority.
        snippets = []
        for snippets_with_trigger in matching_snippets.values():
            highest_priority = max(s.priority for s in snippets_with_trigger)
            snippets.extend(
                s for s in snippets_with_trigger if s.priority == highest_priority
            )

        # For partial matches we are done, but if we want to expand a snippet,
        # we have to go over them again and only keep those with the maximum
        # priority.
        if partial:
            return snippets

        highest_priority = max(s.priority for s in snippets)
        return [s for s in snippets if s.priority == highest_priority]

    def _do_snippet(self, snippet, before):
        """Expands the given snippet, and handles everything that needs to be
        done with it."""
        self._setup_inner_state()

        self._snip_expanded_in_action = False
        self._should_update_textobjects = False

        # Adjust before, maybe the trigger is not the complete word
        text_before = before
        if snippet.matched:
            text_before = before[: -len(snippet.matched)]

        with use_proxy_buffer(self._active_snippets, self._vstate):
            with self._action_context():
                cursor_set_in_action = snippet.do_pre_expand(
                    self._visual_content.text, self._active_snippets
                )

        if cursor_set_in_action:
            text_before = vim_helper.buf.line_till_cursor
            before = vim_helper.buf.line_till_cursor

        with suspend_proxy_edits():
            start = Position(vim_helper.buf.cursor.line, len(text_before))
            end = Position(vim_helper.buf.cursor.line, len(before))
            parent = None
            if self._current_snippet:
                # If cursor is set in pre-action, then action was modified
                # cursor line, in that case we do not need to do any edits, it
                # can break snippet
                if not cursor_set_in_action:
                    # It could be that our trigger contains the content of
                    # TextObjects in our containing snippet. If this is indeed
                    # the case, we have to make sure that those are properly
                    # killed. We do this by pretending that the user deleted
                    # and retyped the text that our trigger matched.
                    edit_actions = [
                        ("D", start.line, start.col, snippet.matched),
                        ("I", start.line, start.col, snippet.matched),
                    ]
                    self._active_snippets[0].replay_user_edits(edit_actions)
                parent = self._current_snippet.find_parent_for_new_to(start)
            snippet_instance = snippet.launch(
                text_before, self._visual_content, parent, start, end
            )
            # Open any folds this might have created
            vim_helper.command("normal! zv")

            self._visual_content.reset()
            self._active_snippets.append(snippet_instance)

            with use_proxy_buffer(self._active_snippets, self._vstate):
                with self._action_context():
                    snippet.do_post_expand(
                        snippet_instance._start,
                        snippet_instance._end,
                        self._active_snippets,
                    )

            self._vstate.remember_buffer(self._active_snippets[0])

            if not self._snip_expanded_in_action:
                self._jump()
            elif self._current_snippet.current_text != "":
                self._jump()
            else:
                self._current_snippet_is_done()

            if self._inside_action:
                self._snip_expanded_in_action = True

    def _try_expand(self, autotrigger_only=False):
        """Try to expand a snippet in the current place."""
        before = vim_helper.buf.line_till_cursor
        snippets = self._snips(before, False, autotrigger_only)
        if snippets:
            # prefer snippets with context if any
            snippets_with_context = [s for s in snippets if s.context]
            if snippets_with_context:
                snippets = snippets_with_context
        if not snippets:
            # No snippet found
            return False
        vim_helper.command("let &undolevels = &undolevels")
        if len(snippets) == 1:
            snippet = snippets[0]
        else:
            snippet = _ask_snippets(snippets)
            if not snippet:
                return True
        self._do_snippet(snippet, before)
        vim_helper.command("let &undolevels = &undolevels")
        return True

    @property
    def _current_snippet(self):
        """The current snippet or None."""
        if not self._active_snippets:
            return None
        return self._active_snippets[-1]

    def _file_to_edit(self, requested_ft, bang):
        """Returns a file to be edited for the given requested_ft.

        If 'bang' is
        empty only private files in g:UltiSnipsSnippetsDir are considered,
        otherwise all files are considered and the user gets to choose.
        """
        snippet_dir = ""
        if vim_helper.eval("exists('g:UltiSnipsSnippetsDir')") == "1":
            dir = vim_helper.eval("g:UltiSnipsSnippetsDir")
            file = self._get_file_to_edit(dir, requested_ft, bang)
            if file:
                return file
            snippet_dir = dir

        if vim_helper.eval("exists('g:UltiSnipsSnippetDirectories')") == "1":
            dirs = vim_helper.eval("g:UltiSnipsSnippetDirectories")
            for dir in dirs:
                file = self._get_file_to_edit(dir, requested_ft, bang)
                if file:
                    return file
                if not snippet_dir:
                    snippet_dir = dir

        home = vim_helper.eval("$HOME")
        if platform.system() == "Windows":
            dir = os.path.join(home, "vimfiles", "UltiSnips")
            file = self._get_file_to_edit(dir, requested_ft, bang)
            if file:
                return file
            if not snippet_dir:
                snippet_dir = dir

        if vim_helper.eval("has('nvim')") == "1":
            xdg_home_config = vim_helper.eval("$XDG_CONFIG_HOME") or os.path.join(
                home, ".config"
            )
            dir = os.path.join(xdg_home_config, "nvim", "UltiSnips")
            file = self._get_file_to_edit(dir, requested_ft, bang)
            if file:
                return file
            if not snippet_dir:
                snippet_dir = dir

        dir = os.path.join(home, ".vim", "UltiSnips")
        file = self._get_file_to_edit(dir, requested_ft, bang)
        if file:
            return file
        if not snippet_dir:
            snippet_dir = dir

        return self._get_file_to_edit(snippet_dir, requested_ft, bang, True)

    def _get_file_to_edit(
        self, snippet_dir, requested_ft, bang, allow_empty=False
    ):  # pylint: disable=no-self-use
        potentials = set()
        filetypes = []
        if requested_ft:
            filetypes.append(requested_ft)
        else:
            if bang:
                filetypes.extend(self.get_buffer_filetypes())
            else:
                filetypes.append(self.get_buffer_filetypes()[0])

        for ft in filetypes:
            potentials.update(find_snippet_files(ft, snippet_dir))
            potentials.add(os.path.join(snippet_dir, ft + ".snippets"))
            if bang:
                potentials.update(find_all_snippet_files(ft))

        potentials = set(os.path.realpath(os.path.expanduser(p)) for p in potentials)

        if len(potentials) > 1:
            files = sorted(potentials)
            formatted = [
                as_unicode("%i: %s") % (i, escape(fn, "\\"))
                for i, fn in enumerate(files, 1)
            ]
            file_to_edit = _ask_user(files, formatted)
            if file_to_edit is None:
                return ""
        else:
            file_to_edit = potentials.pop()

        if not allow_empty and not os.path.exists(file_to_edit):
            return ""

        dirname = os.path.dirname(file_to_edit)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return file_to_edit

    @contextmanager
    def _action_context(self):
        try:
            old_flag = self._inside_action
            self._inside_action = True
            yield
        finally:
            self._inside_action = old_flag

    @err_to_scratch_buffer.wrap
    def _track_change(self):
        self._should_update_textobjects = True

        try:
            inserted_char = vim_helper.as_unicode(vim_helper.eval("v:char"))
        except UnicodeDecodeError:
            return

        if sys.version_info >= (3, 0):
            if isinstance(inserted_char, bytes):
                return
        else:
            if not isinstance(inserted_char, unicode):
                return

        try:
            if inserted_char == "":
                before = vim_helper.buf.line_till_cursor

                if (
                    before
                    and before[-1] == self._last_change[0]
                    or self._last_change[1] != vim_helper.buf.cursor
                ):
                    self._try_expand(autotrigger_only=True)
        finally:
            self._last_change = (inserted_char, vim_helper.buf.cursor)

        if self._should_reset_visual and self._visual_content.mode == "":
            self._visual_content.reset()

        self._should_reset_visual = True

    @err_to_scratch_buffer.wrap
    def _refresh_snippets(self):
        for _, source in self._snippet_sources:
            source.refresh()


UltiSnips_Manager = SnippetManager(  # pylint:disable=invalid-name
    vim.eval("g:UltiSnipsExpandTrigger"),
    vim.eval("g:UltiSnipsJumpForwardTrigger"),
    vim.eval("g:UltiSnipsJumpBackwardTrigger"),
)
