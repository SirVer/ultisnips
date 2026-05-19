#!/usr/bin/env python3

"""Contains the SnippetManager facade used by all Vim Functions."""

from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import vim

from UltiSnips import err_to_scratch_buffer, vim_helper
from UltiSnips.buffer_proxy import suspend_proxy_edits, use_proxy_buffer
from UltiSnips.change_provider import (
    DROP_SNIPPET,
    NvimChangeProvider,
    VimChangeProvider,
)
from UltiSnips.position import JumpDirection, Position
from UltiSnips.snippet.definition import UltiSnipsSnippetDefinition
from UltiSnips.snippet.source import (
    AddedSnippetsSource,
    SnipMateFileSource,
    UltiSnipsFileSource,
    find_all_snippet_directories,
    find_snippet_files,
)
from UltiSnips.snippet.source.file.common import (
    normalize_file_path,
)
from UltiSnips.text import escape
from UltiSnips.vim_state import VimState, VisualContentPreserver


def _ask_user(a, formatted):
    """Asks the user using inputlist() and returns the selected element or
    None."""
    try:
        rv = vim_helper.eval(f"inputlist({vim_helper.escape(formatted)})")
        if rv is None or rv == "0":
            return None
        rv = int(rv)
        # Vim's inputlist() returns -1 when the user clicks outside the menu,
        # and may return values outside `1..len(a)` when the user types a
        # number that doesn't correspond to a listed snippet (e.g. by clicking
        # the prompt line below the list). Treat any out-of-range answer as a
        # cancellation rather than picking an arbitrary entry.
        if rv < 1 or rv > len(a):
            return None
        return a[rv - 1]
    except vim_helper.error:
        # Likely "invalid expression", but might be translated. We have no way
        # of knowing the exact error, therefore, we ignore all errors silently.
        return None
    except KeyboardInterrupt:
        return None


def _show_user_warning(msg):
    """Shows a Vim warning message to the user."""
    vim.command("echohl WarningMsg")
    escaped = msg.replace('"', '\\"')
    vim.command(f'echom "{escaped}"')
    vim.command("echohl None")


def _ask_snippets(snippets):
    """Given a list of snippets, ask the user which one they want to use, and
    return it."""
    _bs = "\\"
    display = [
        f"{i + 1}: {escape(s.description, _bs)} ({escape(s.location, _bs)})"
        for i, s in enumerate(snippets)
    ]
    return _ask_user(snippets, display)


def _select_and_create_file_to_edit(potentials: set[str]) -> str:
    assert len(potentials) >= 1

    file_to_edit = ""
    if len(potentials) > 1:
        files = sorted(potentials)
        exists = [Path(f).exists() for f in files]
        _bs = "\\"
        formatted = [
            f"{'*' if exists else ' '} {i}: {escape(fn, _bs)}"
            for i, (fn, exists) in enumerate(zip(files, exists, strict=False), 1)
        ]
        file_to_edit = _ask_user(files, formatted)
        if file_to_edit is None:
            return ""
    else:
        file_to_edit = potentials.pop()

    dirname = Path(file_to_edit).parent
    if not dirname.exists():
        dirname.mkdir(parents=True)

    return file_to_edit


def _get_potential_snippet_filenames_to_edit(
    snippet_dir: str, filetypes: str
) -> set[str]:
    potentials = set()
    for ft in filetypes:
        ft_snippets_files = find_snippet_files(ft, snippet_dir)
        potentials.update(ft_snippets_files)
        if not ft_snippets_files:
            # If there is no snippet file yet, we just default to `ft.snippets`.
            fpath = str(Path(snippet_dir) / (ft + ".snippets"))
            fpath = normalize_file_path(fpath)
            potentials.add(fpath)
    return potentials


class SnippetManager:
    """The main entry point for all UltiSnips functionality.

    All Vim functions call methods in this class.

    """

    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        self.expand_trigger = expand_trigger
        self.forward_trigger = forward_trigger
        self.backward_trigger = backward_trigger
        self._inner_state_up = False
        self._snippet_buffer_number = None
        self._supertab_keys = None

        self._active_snippets = []
        self._added_buffer_filetypes = defaultdict(list)
        self._removed_buffer_filetypes = defaultdict(set)

        self._vstate = VimState()
        self._visual_content = VisualContentPreserver()

        self._snippet_sources = []

        self._snip_expanded_in_action = False
        self._inside_action = False

        self._last_change = ("", Position(-1, -1))

        self._added_snippets_source = AddedSnippetsSource()
        self.register_snippet_source("ultisnips_files", UltiSnipsFileSource())
        self.register_snippet_source("added", self._added_snippets_source)

        enable_snipmate = vim.vars.get("UltiSnipsEnableSnipMate", 1)
        if int(enable_snipmate):
            self.register_snippet_source("snipmate_files", SnipMateFileSource())

        self._autotrigger = bool(int(vim.vars.get("UltiSnipsAutoTrigger", 1)))

        self._should_update_textobjects = False
        self._should_reset_visual = False

        if int(vim_helper.eval("has('nvim')")):
            self._change_provider = NvimChangeProvider()
        else:
            self._change_provider = VimChangeProvider()
        assert self._change_provider is not None

        self._reinit()

    @err_to_scratch_buffer.wrap
    def jump_forwards(self):
        """Jumps to the next tabstop."""
        vim.vars["ulti_jump_forwards_res"] = 1
        vim.command("let &g:undolevels = &g:undolevels")
        if not self._jump(JumpDirection.FORWARD):
            vim.vars["ulti_jump_forwards_res"] = 0
            return self._handle_failure(self.forward_trigger)
        return None

    @err_to_scratch_buffer.wrap
    def jump_backwards(self):
        """Jumps to the previous tabstop."""
        vim.vars["ulti_jump_backwards_res"] = 1
        vim.command("let &g:undolevels = &g:undolevels")
        if not self._jump(JumpDirection.BACKWARD):
            vim.vars["ulti_jump_backwards_res"] = 0
            return self._handle_failure(self.backward_trigger)
        return None

    @err_to_scratch_buffer.wrap
    def expand(self):
        """Try to expand a snippet at the current position."""
        vim.vars["ulti_expand_res"] = 1
        if not self._try_expand():
            vim.vars["ulti_expand_res"] = 0
            self._handle_failure(self.expand_trigger, True)

    @err_to_scratch_buffer.wrap
    def expand_or_jump(self):
        """This function is used for people who want to have the same trigger
        for expansion and forward jumping.

        It first tries to expand a snippet, if this fails, it tries to
        jump forward.

        """
        vim.vars["ulti_expand_or_jump_res"] = 1
        rv = self._try_expand()
        if not rv:
            vim.vars["ulti_expand_or_jump_res"] = 2
            rv = self._jump(JumpDirection.FORWARD)
        if not rv:
            vim.vars["ulti_expand_or_jump_res"] = 0
            self._handle_failure(self.expand_trigger, True)

    @err_to_scratch_buffer.wrap
    def jump_or_expand(self):
        """This function is used for people who want to have the same trigger
        for expansion and forward jumping.

        It first tries to jump forward, if this fails, it tries to
        expand a snippet.

        """
        vim.vars["ulti_expand_or_jump_res"] = 2
        rv = self._jump(JumpDirection.FORWARD)
        if not rv:
            vim.vars["ulti_expand_or_jump_res"] = 1
            rv = self._try_expand()
        if not rv:
            vim.vars["ulti_expand_or_jump_res"] = 0
            self._handle_failure(self.expand_trigger, True)

    @err_to_scratch_buffer.wrap
    def snippets_in_current_scope(self, search_all):
        """Returns the snippets that could be expanded to Vim as a global
        variable."""
        before = "" if search_all else vim_helper.buf.line_till_cursor
        snippets = self._snips(before, True)

        # Sort snippets alphabetically
        snippets.sort(key=lambda x: x.trigger)
        ulti_dict = {}
        ulti_dict_info = {}
        for snip in snippets:
            description = snip.description[
                snip.description.find(snip.trigger) + len(snip.trigger) + 2 :
            ]

            location = snip.location if snip.location else ""

            key = snip.trigger

            # remove surrounding "" or '' in snippet description if it exists
            if (
                len(description) > 2
                and description[0] == description[-1]
                and description[0] in "'\""
            ):
                description = description[1:-1]

            ulti_dict[key] = description

            ulti_dict_info[key] = {
                "description": description,
                "location": location,
            }

        # Assign the full dict at once rather than mutating
        # vim.vars["current_ulti_dict"][key] — neovim's Python API returns a
        # copy for dict values, so per-key mutation is silently lost.
        vim.vars["current_ulti_dict"] = ulti_dict
        vim.vars["current_ulti_dict_info"] = ulti_dict_info

    @err_to_scratch_buffer.wrap
    def list_snippets(self):
        """Shows the snippets that could be expanded to the User and let her
        select one."""
        before = vim_helper.buf.line_till_cursor
        snippets = self._snips(before, True)

        if len(snippets) == 0:
            self._handle_failure(vim_helper.as_str(vim.vars["UltiSnipsListSnippets"]))
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

    def all_snippet_files_for(self, ft):
        """Returns every snippet file that any registered source would load
        for filetype 'ft'. Used by :UltiSnipsEdit! to build the picker
        list. Sources that don't back snippets with files contribute an
        empty set via the base-class default."""
        files = set()
        for _, source in self._snippet_sources:
            files.update(source.get_all_snippet_files_for(ft))
        return files

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
        removed = self._removed_buffer_filetypes[vim_helper.buf.number]
        fts = (
            self._added_buffer_filetypes[vim_helper.buf.number]
            + vim_helper.buf.filetypes
            + ["all"]
        )
        return [ft for ft in fts if ft not in removed]

    def add_buffer_filetypes(self, filetypes: str):
        """'filetypes' is a dotted filetype list, for example 'cuda.cpp'"""
        buf_fts = self._added_buffer_filetypes[vim_helper.buf.number]
        removed = self._removed_buffer_filetypes[vim_helper.buf.number]
        idx = -1
        for ft in filetypes.split("."):
            ft = ft.strip()
            if not ft:
                continue
            # Adding a filetype overrides a previous removal so the user can
            # cleanly re-enable a filetype they had disabled.
            removed.discard(ft)
            try:
                idx = buf_fts.index(ft)
            except ValueError:
                self._added_buffer_filetypes[vim_helper.buf.number].insert(idx + 1, ft)
                idx += 1

    def remove_buffer_filetypes(self, filetypes: str):
        """Disable snippets for the given filetypes in the current buffer.

        Accepts the same dotted filetype syntax as |add_buffer_filetypes|
        (e.g. 'html.css'). Filetypes that came from `&filetype`, from a
        previous `add_buffer_filetypes`, or implicitly through `all` are all
        eligible to be removed. Removal is persistent for the lifetime of the
        buffer; a later `add_buffer_filetypes` re-enables the filetype.
        """
        buf_fts = self._added_buffer_filetypes[vim_helper.buf.number]
        removed = self._removed_buffer_filetypes[vim_helper.buf.number]
        for ft in filetypes.split("."):
            ft = ft.strip()
            if not ft:
                continue
            removed.add(ft)
            if ft in buf_fts:
                buf_fts.remove(ft)

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
            # `:bd!` (and similar buffer-switch commands) fire CursorMoved on
            # the new buffer before the BufEnter-scheduled `_leaving_buffer`
            # timer callback runs. Reconciling the snippet's text objects
            # against an unrelated buffer corrupts both the buffer and the
            # snippet state — drop the snippets here so the caller sees a
            # clean slate.
            #
            # Excursions into auxiliary windows (the preview window,
            # quickfix/loclist, neovim floats) are different: the user
            # expects to come back to the snippet, so just bail out
            # without touching the snippet state. `UltiSnips#LeavingBuffer`
            # already applies the same classification.
            if vim.current.buffer.number != self._snippet_buffer_number:
                if vim_helper.eval("UltiSnips#IsAuxWindow(winnr())") == "1":
                    return
                self._leaving_buffer()
                return

            es = self._change_provider.consume_edits(
                vim_helper.buf, self._active_snippets[0], self._vstate
            )
            if es is DROP_SNIPPET:
                # Buffer has diverged from the snippet's tracked state so
                # heavily that reconciling would hang diff() or corrupt
                # the text-object tree. Abandon the snippet cleanly.
                while self._active_snippets:
                    self._current_snippet_is_done()
                self._reinit()
                return
            if es is not None:
                self._active_snippets[0].replay_user_edits(es, self._ctab)

        self._check_if_still_inside_snippet()
        if self._active_snippets:
            with self._change_provider.suppressed():
                self._active_snippets[0].update_textobjects(vim_helper.buf, self._ctab)
                self._vstate.remember_buffer(self._active_snippets[0])

    def _setup_inner_state(self):
        """Map keys and create autocommands that should only be defined when a
        snippet is active."""
        if self._inner_state_up:
            return
        if self.expand_trigger != self.forward_trigger:
            vim.command(
                "inoremap <buffer><nowait><silent> "
                + self.forward_trigger
                + " <C-R>=UltiSnips#JumpForwards()<cr>"
            )
            vim.command(
                "snoremap <buffer><nowait><silent> "
                + self.forward_trigger
                + " <Esc>:call UltiSnips#JumpForwards()<cr>"
            )
        vim.command(
            "inoremap <buffer><nowait><silent> "
            + self.backward_trigger
            + " <C-R>=UltiSnips#JumpBackwards()<cr>"
        )
        vim.command(
            "snoremap <buffer><nowait><silent> "
            + self.backward_trigger
            + " <Esc>:call UltiSnips#JumpBackwards()<cr>"
        )

        # Setup the autogroups.
        vim.command("augroup UltiSnips")
        vim.command("autocmd!")
        vim.command("autocmd CursorMovedI * call UltiSnips#CursorMoved()")
        vim.command("autocmd CursorMoved * call UltiSnips#CursorMoved()")

        vim.command("autocmd InsertLeave * call UltiSnips#LeavingInsertMode()")

        vim.command("autocmd BufEnter * call UltiSnips#LeavingBuffer()")
        vim.command("autocmd CmdwinEnter * call UltiSnips#LeavingBuffer()")
        vim.command("autocmd CmdwinLeave * call UltiSnips#LeavingBuffer()")

        # Also exit the snippet when we enter a unite complete buffer.
        vim.command("autocmd Filetype unite call UltiSnips#LeavingBuffer()")

        vim.command("augroup END")

        vim.command("silent doautocmd <nomodeline> User UltiSnipsEnterFirstSnippet")
        self._change_provider.attach(vim.current.buffer.number)
        self._snippet_buffer_number = vim.current.buffer.number
        self._inner_state_up = True

    def _teardown_inner_state(self):
        """Reverse _setup_inner_state."""
        if not self._inner_state_up:
            return
        # Restore cached registers now: the InsertLeave autocmd that would
        # normally call _leaving_insert_mode is removed below, so without
        # this the clobbering done by the LAST placeholder edit would
        # never be undone. Then drop the cache so the next snippet starts
        # from a clean slate.
        self._vstate.restore_unnamed_register()
        self._vstate.reset_register_cache()
        try:
            vim.command("silent doautocmd <nomodeline> User UltiSnipsExitLastSnippet")
            if self.expand_trigger != self.forward_trigger:
                vim.command(f"iunmap <buffer> {self.forward_trigger}")
                vim.command(f"sunmap <buffer> {self.forward_trigger}")
            vim.command(f"iunmap <buffer> {self.backward_trigger}")
            vim.command(f"sunmap <buffer> {self.backward_trigger}")
            vim.command("augroup UltiSnips")
            vim.command("autocmd!")
            vim.command("augroup END")
        except vim_helper.error:
            # This happens when a preview window was opened. This issues
            # CursorMoved, but not BufLeave. We have no way to unmap, until we
            # are back in our buffer
            pass
        finally:
            self._change_provider.detach()
            self._snippet_buffer_number = None
            self._inner_state_up = False

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
        snippet_instance = self._active_snippets[-1]
        snippets_stack = self._active_snippets[:]
        with (
            use_proxy_buffer(snippets_stack, self._vstate, self._change_provider),
            self._action_context(),
        ):
            snippet_instance.snippet.do_post_finish(snippet_instance)
        self._active_snippets.pop()
        if not self._active_snippets:
            self._teardown_inner_state()

    def _jump(self, jump_direction: JumpDirection):
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

            move_cmd = ""
            if self._current_snippet:
                ntab = self._current_snippet.select_next_tab(jump_direction)
                if ntab:
                    if self._current_snippet.snippet.has_option("s"):
                        lineno = vim_helper.buf.cursor.line
                        vim_helper.buf[lineno] = vim_helper.buf[lineno].rstrip()
                    with self._change_provider.suppressed():
                        move_cmd = vim_helper.select(ntab.start, ntab.end)
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
                        self._active_snippets[0].update_textobjects(
                            vim_helper.buf, self._ctab
                        )
                        # Open any folds this might have created
                        vim.command("normal! zv")
                        self._vstate.remember_buffer(self._active_snippets[0])

                    if ntab.number == 0 and self._active_snippets:
                        # The 'x' option asks for normal mode once the snippet
                        # reaches its final tabstop. Capture the request before
                        # popping the snippet, then suppress the queued
                        # insert-mode re-entry below.
                        finish_in_normal_mode = (
                            self._current_snippet.snippet.has_option("x")
                        )
                        self._current_snippet_is_done()
                        if finish_in_normal_mode:
                            # Queue an `<Esc>` at the *front* of the typeahead
                            # (the `i` flag) so it is processed before any
                            # follow-up user keystrokes still in the input
                            # queue. The deferred `:stopinsert` queued inside
                            # `vim_helper.select()` is not reliably consumed
                            # between this Python callback returning and the
                            # next key being processed; an explicit prepended
                            # `<Esc>` guarantees normal mode.
                            vim.command(r'call feedkeys("\<Esc>", "in")')
                            move_cmd = ""
                else:
                    # This really shouldn't happen, because a snippet should
                    # have been popped when its final tabstop was used.
                    # Cleanup by removing current snippet and recursing.
                    self._current_snippet_is_done()
                    jumped = self._jump(jump_direction)

            if jumped:
                if self._ctab:
                    self._vstate.remember_position()
                    self._vstate.remember_unnamed_register(self._ctab.current_text)
                if not ntab_short_and_near:
                    self._ignore_movements = True
                # Let users hook a global handler that runs every time the
                # cursor lands on a new tabstop -- including the initial
                # expansion, since _do_snippet's first jump comes through
                # this method. The final $0 is excluded because the snippet
                # is torn down right after, and `UltiSnipsExitLastSnippet`
                # is the right hook for that.
                if self._ctab is None or self._ctab.number != 0:
                    vim.command("silent doautocmd <nomodeline> User UltiSnipsJumped")

            # Reset the flag so we observe only what *this* post_jump action
            # does. _do_snippet sets it to True at its tail when called from
            # within an action context, and we read it back below to decide
            # whether our move command is still needed.
            snip_expanded_in_action = False
            if len(stack_for_post_jump) > 0 and ntab is not None:
                # Run the post_jump action inside an action context so that a
                # nested `snip.expand_anon()` inside it gets recorded in
                # `_snip_expanded_in_action`. We use that flag below to decide
                # whether the move command we built for this jump still needs
                # to be fed — if the action expanded a new snippet, that
                # snippet's own _jump already queued the right mode-entry
                # keys and our outer move command would just override them.
                self._snip_expanded_in_action = False
                with (
                    use_proxy_buffer(
                        stack_for_post_jump, self._vstate, self._change_provider
                    ),
                    self._action_context(),
                ):
                    snippet_for_action.snippet.do_post_jump(
                        ntab.number,
                        -1 if jump_direction == JumpDirection.BACKWARD else 1,
                        stack_for_post_jump,
                        snippet_for_action,
                    )
                snip_expanded_in_action = self._snip_expanded_in_action

            if move_cmd and not snip_expanded_in_action:
                # Rebuild `move_cmd` against `ntab`'s current
                # positions. If the action edited the buffer the
                # tabstop's start/end have already been shifted to
                # follow; the string we captured before the action ran
                # would now drive the cursor to the old offsets and the
                # select-mode range would land in the wrong place. The
                # rebuild also re-anchors the cursor at the new start,
                # which is the intent when an action sets `snip.cursor`
                # to mirror a buffer shift it made. See #1013.
                move_cmd = vim_helper.select(ntab.start, ntab.end)
                if move_cmd:
                    vim_helper.feedkeys(move_cmd)

        return jumped

    def _leaving_insert_mode(self):
        """Called whenever we leave the insert mode."""
        self._vstate.restore_unnamed_register()

    def _handle_failure(self, trigger, pass_through=False):
        """Mainly make sure that we play well with SuperTab."""
        if trigger.lower() in ("<tab>", "<s-tab>") or (
            pass_through and int(vim.vars.get("UltiSnipsInsertTriggerOnNoMatch", 1))
        ):
            feedkey = "\\" + trigger
        else:
            feedkey = None
        mode = "n"
        if not self._supertab_keys:
            fwd = vim.vars.get("SuperTabMappingForward", None)
            if fwd is not None:
                self._supertab_keys = (
                    vim_helper.as_str(fwd),
                    vim_helper.as_str(vim.vars.get("SuperTabMappingBackward", b"")),
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
            vim.command(f"return SuperTab({vim_helper.escape(mode)})")
        elif feedkey:
            vim.command(f"return {vim_helper.escape(feedkey)}")

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

        with (
            use_proxy_buffer(
                self._active_snippets, self._vstate, self._change_provider
            ),
            self._action_context(),
        ):
            cursor_set_in_action = snippet.do_pre_expand(
                self._visual_content.text, self._active_snippets
            )

        # `pre_expand` may have nested an anonymous snippet (the "wrap"
        # pattern from #1579 / #1592). Capture that fact before our own
        # body is launched so the post-expand book-keeping below can
        # tell apart "inner was already there before us" from "inner
        # came and went during our `post_expand`".
        pre_expand_nested = self._snip_expanded_in_action

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
            vim.command("normal! zv")

            self._visual_content.reset()
            self._active_snippets.append(snippet_instance)

            # Park the cursor at the snippet's end before `post_expand`
            # runs. Without this, the cursor sits wherever the buffer
            # write left it — typically at the trigger's old position,
            # which is *inside* the body for a non-empty snippet. Any
            # `snip.expand_anon` in the action would then splice the
            # anon body into the middle of ours instead of appending it
            # cleanly. See #1434.
            vim_helper.buf.cursor = Position(
                snippet_instance.end.line, snippet_instance.end.col
            )
            with (
                use_proxy_buffer(
                    self._active_snippets, self._vstate, self._change_provider
                ),
                self._action_context(),
            ):
                snippet.do_post_expand(
                    snippet_instance.start,
                    snippet_instance.end,
                    self._active_snippets,
                )

            self._vstate.remember_buffer(self._active_snippets[0])
            self._change_provider.reset()

            # Four shapes show up here depending on which action
            # nested another snippet via `snip.expand_anon`:
            #
            #   1. No nesting. `_snip_expanded_in_action` is False.
            #      Jump into our first tabstop as usual (this is also
            #      what fires `post_jump` on the implicit `$0` for
            #      bodyless snippets).
            #
            #   2. `pre_expand` nested. The action ran *before* our
            #      `launch`, so the inner snippet was appended first and
            #      our own append put us on top of it. `_active_snippets[-1]`
            #      is still `snippet_instance`. If outer has its own
            #      body the user expects to fill outer's tabstops first
            #      (#1579 / #1592 wrap pattern), so jump; if outer is a
            #      hollow wrapper (`current_text == ""`) pop it
            #      immediately.
            #
            #   3. `post_expand` nested and the inner is still live. The
            #      action ran *after* our append, so the inner sits on
            #      top of us. The nested `_do_snippet` already jumped to
            #      its own first tabstop; a second jump here would skip
            #      it. Drop ourselves from the stack so the inner is the
            #      live snippet.
            #
            #   4. `post_expand` nested an inner that finished its own
            #      jumps inside the action (e.g. anon body with only `$0`
            #      or plain text — `_jump` selects `$0` and pops it).
            #      Outer's `$0` tabstop was stretched by
            #      `_child_has_moved` to span the inner's text; jumping
            #      into it now would re-select the entire inner body and
            #      derail the buffer state. Outer has nothing left to
            #      offer, so finish it cleanly. See #1688.
            post_expand_nested_and_popped = (
                self._snip_expanded_in_action
                and not pre_expand_nested
                and self._active_snippets
                and self._active_snippets[-1] is snippet_instance
            )
            if (
                self._snip_expanded_in_action
                and self._active_snippets
                and self._active_snippets[-1] is not snippet_instance
            ):
                # Shape 3 — inner is still on the stack.
                self._active_snippets.remove(snippet_instance)
                if not self._active_snippets:
                    self._teardown_inner_state()
            elif post_expand_nested_and_popped:
                # Shape 4 — post_expand nested an inner that already
                # finished. Pop outer; jumping would re-select the
                # inner body that outer's `$0` now wraps.
                self._current_snippet_is_done()
            elif (
                not self._snip_expanded_in_action
                or self._current_snippet.current_text != ""
            ):
                self._jump(JumpDirection.FORWARD)
            else:
                self._current_snippet_is_done()

            if self._inside_action:
                self._snip_expanded_in_action = True

    def _can_expand(self, autotrigger_only=False):
        before = vim_helper.buf.line_till_cursor
        return before, self._snips(before, False, autotrigger_only)

    def _try_expand(self, autotrigger_only=False):
        """Try to expand a snippet in the current place."""
        # Drain buffer edits queued while CursorMovedI could not fire —
        # notably while the completion popup was visible. Without this the
        # text-object tree is stale and _do_snippet's replay crosses
        # placeholder boundaries, deleting sibling tabstops. See #1380/#1327.
        if self._active_snippets:
            self._cursor_moved()
        before, snippets = self._can_expand(autotrigger_only)
        if snippets:
            # prefer snippets with context if any
            snippets_with_context = [s for s in snippets if s.context]
            if snippets_with_context:
                snippets = snippets_with_context
        if not snippets:
            # No snippet found
            return False
        vim.command("let &g:undolevels = &g:undolevels")
        if len(snippets) == 1:
            snippet = snippets[0]
        else:
            snippet = _ask_snippets(snippets)
            if not snippet:
                return True
        self._do_snippet(snippet, before)
        vim.command("let &g:undolevels = &g:undolevels")
        return True

    def can_expand(self, autotrigger_only=False):
        """Check if we would be able to successfully find a
        snippet in the current position."""
        return bool(self._can_expand(autotrigger_only)[1])

    def can_jump(self, direction):
        if self._current_snippet is None:
            return False
        return self._current_snippet.has_next_tab(direction)

    def can_jump_forwards(self):
        return self.can_jump(JumpDirection.FORWARD)

    def can_jump_backwards(self):
        return self.can_jump(JumpDirection.BACKWARD)

    def _toggle_autotrigger(self):
        self._autotrigger = not self._autotrigger
        return self._autotrigger

    @property
    def _current_snippet(self):
        """The current snippet or None."""
        if not self._active_snippets:
            return None
        return self._active_snippets[-1]

    def _file_to_edit(self, requested_ft, bang):
        """Returns a file to be edited for the given requested_ft.

        If 'bang' is empty a reasonable first choice is opened (see docs), otherwise
        all files are considered and the user gets to choose.
        """
        filetypes = []
        if requested_ft:
            filetypes.append(requested_ft)
        else:
            if bang:
                filetypes.extend(self.get_buffer_filetypes())
            else:
                filetypes.append(self.get_buffer_filetypes()[0])

        potentials = set()

        dot_vim_dirs = vim_helper.get_dot_vim()
        all_snippet_directories = find_all_snippet_directories()
        snippet_storage_dir = vim.vars.get(
            "UltiSnipsSnippetStorageDirectoryForUltiSnipsEdit", None
        )
        if snippet_storage_dir is not None:
            snippet_storage_dir = vim_helper.as_str(snippet_storage_dir)
            full_path = str(Path(snippet_storage_dir).expanduser())
            potentials.update(
                _get_potential_snippet_filenames_to_edit(full_path, filetypes)
            )
        if len(all_snippet_directories) == 1:
            # Most likely the user has set g:UltiSnipsSnippetDirectories to a
            # single absolute path.
            potentials.update(
                _get_potential_snippet_filenames_to_edit(
                    all_snippet_directories[0], filetypes
                )
            )

        has_storage_dir = snippet_storage_dir is not None
        if (len(all_snippet_directories) != 1 and not has_storage_dir) or (
            has_storage_dir and bang
        ):
            # Likely the array contains things like ["UltiSnips",
            # "mycoolsnippets"] There is no more obvious way to edit than in
            # the users vim config directory.
            #
            # `dot_vim_dirs` has already been canonicalised by
            # `vim_helper.get_dot_vim()`, but the snippet dirs come straight
            # from a runtimepath glob and keep symlinks intact. A user with
            # a symlinked snippets directory (or, on macOS, a `$HOME` that
            # lives under the auto-resolved `/private/var/...`) would see
            # the two sides disagree and never populate `potentials`
            # (#1543). Compare resolved forms so the check is independent
            # of which leg of the path is a symlink.
            for snippet_dir in all_snippet_directories:
                snippet_parent_resolved = Path(snippet_dir).parent.resolve()
                for dot_vim_dir in dot_vim_dirs:
                    if Path(dot_vim_dir).resolve() != snippet_parent_resolved:
                        continue
                    potentials.update(
                        _get_potential_snippet_filenames_to_edit(snippet_dir, filetypes)
                    )

        if bang:
            for ft in filetypes:
                potentials.update(self.all_snippet_files_for(ft))
        else:
            if not potentials:
                _show_user_warning(
                    f"UltiSnips was not able to find a default directory for snippets. "
                    f"Do any of {dot_vim_dirs} exist AND contain "
                    f"any of the folders in g:UltiSnipsSnippetDirectories ? "
                    f"With default vim settings that would be: ~/.vim/UltiSnips "
                    f"Try :UltiSnipsEdit! instead of :UltiSnipsEdit."
                )
                return ""
        return _select_and_create_file_to_edit(potentials)

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
            inserted_char = vim_helper.eval("v:char")
        except UnicodeDecodeError:
            return

        if isinstance(inserted_char, bytes):
            return

        try:
            if inserted_char == "":
                before = vim_helper.buf.line_till_cursor

                if (
                    self._autotrigger
                    and before
                    and self._last_change[0] != ""
                    and before[-1] == self._last_change[0]
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


UltiSnips_Manager = SnippetManager(
    vim_helper.as_str(vim.vars["UltiSnipsExpandTrigger"]),
    vim_helper.as_str(vim.vars["UltiSnipsJumpForwardTrigger"]),
    vim_helper.as_str(vim.vars["UltiSnipsJumpBackwardTrigger"]),
)
