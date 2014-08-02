#!/usr/bin/env python
# encoding: utf-8

"""Collects snippet sources and get all matching snippets."""

from collections import defaultdict

from UltiSnips import _vim
from UltiSnips._diff import diff, guess_edit
from UltiSnips.key_mapper import KeyMapper
from UltiSnips.position import Position
from UltiSnips.vim_state import VimState, VisualContentPreserver


class SnippetPerformer(object):
    """See module doc."""

    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        self._snippet_sources = {}
        self._inner_key_mapper = KeyMapper(
                expand_trigger, forward_trigger, backward_trigger)
        self._csnippets = []
        self._vstate = VimState()
        self._visual_content = VisualContentPreserver()

        self.reinit()

    def register(self, name, snippet_source):
        """Registers a new 'snippet_source' with the given 'name'. The given
        class must be an instance of SnippetSource. This source will be queried
        for snippets."""
        self._snippet_sources[name] = snippet_source

    def unregister(self, name):
        """Unregister the source with the given 'name'. Does nothing if it is
        not registered.  This method is used by test currently."""
        self._snippet_sources.pop(name, None)

    def get_source(self, name):
        """Get the snippet source by the registered name.  Raise
        KeyError if the name is not registered."""
        return self._snippet_sources[name]

    def _ensure(self, filetypes):
        """Ensure all sources in this collector for given filetypes.
        """
        for source in self._snippet_sources.values():
            source.ensure(filetypes)

    def _clear_priority(self, filetypes):
        """Get maximum clear priority for given filetypes.
        """
        clear_priority = None
        for source in self._snippet_sources.values():
            source_clear_priority = source.get_clear_priority(filetypes)
            if source_clear_priority is not None and (clear_priority is
                    None or source_clear_priority > clear_priority):
                clear_priority = source_clear_priority
        return clear_priority

    def _cleared(self, filetypes):
        """Get cleared snippet information by given filetypes.
        """
        cleared = {}
        for source in self._snippet_sources.values():
            for key, value in source.get_cleared(filetypes).items():
                if key not in cleared or value > cleared[key]:
                    cleared[key] = value
        return cleared

    def _matching_snippets(self, filetypes, before, partial):
        """Get all non-cleared matching snippets.  It is a dict maps
        trigger to a list of matching snippets.
        """
        self._ensure(filetypes)

        matching_snippets = defaultdict(list)
        clear_priority = self._clear_priority(filetypes)
        cleared = self._cleared(filetypes)
        for source in self._snippet_sources.values():
            for snippet in source.get_snippets(filetypes, before, partial):
                if ((clear_priority is None
                        or snippet.priority > clear_priority
                    ) and (
                        snippet.trigger not in cleared or
                        snippet.priority > cleared[snippet.trigger])):
                    matching_snippets[snippet.trigger].append(snippet)
        return matching_snippets

    def _partial_match_snippets(self, filetypes, before, partial):
        """Get partial matched snippets.
        """
        matching_snippets = self._matching_snippets(filetypes, before, partial)
        if not matching_snippets:
            return []

        # Filter duplicates and only keep the one with the highest
        # priority.
        snippets = []
        for snippets_with_trigger in matching_snippets.values():
            highest_priority = max(s.priority for s in snippets_with_trigger)
            snippets.extend(s for s in snippets_with_trigger
                    if s.priority == highest_priority)
        return snippets

    def snips(self, filetypes, before, partial):
        """Get all uncleared matched snippets with highest priority.
        """
        partial_match = self._partial_match_snippets(
                filetypes, before, partial)
        # For partial matches we are done, but if we want to expand a snippet,
        # we have to go over them again and only keep those with the maximum
        # priority.
        if partial or not partial_match:
            return partial_match

        highest_priority = max(s.priority for s in partial_match)
        return [s for s in partial_match if s.priority == highest_priority]

    @property
    def _cs(self):
        """The current snippet or None."""
        if not len(self._csnippets):
            return None
        return self._csnippets[-1]

    def reinit(self):
        """Resets transient state."""
        self._ctab = None
        self._ignore_movements = False

    def check_if_still_inside_snippet(self):
        """Checks if the cursor is outside of the current snippet."""
        if self._cs and (
            not self._cs.start <= _vim.buf.cursor <= self._cs.end
        ):
            self.current_snippet_is_done()
            self.reinit()
            self.check_if_still_inside_snippet()

    def current_snippet_is_done(self):
        """The current snippet should be terminated."""
        self._csnippets.pop()
        if not self._csnippets:
            self._inner_key_mapper.unmap_inner_keys()

    def jump(self, backwards=False):
        """Helper method that does the actual jump."""
        jumped = False
        # If next tab has length 1 and the distance between itself and
        # self._ctab is 1 then there is 1 less CursorMove events.  We cannot
        #ignore next movement in such case.
        ntab_short_and_near = False
        if self._cs:
            ntab = self._cs.select_next_tab(backwards)
            if ntab:
                if self._cs.snippet.has_option("s"):
                    lineno = _vim.buf.cursor.line
                    _vim.buf[lineno] = _vim.buf[lineno].rstrip()
                _vim.select(ntab.start, ntab.end)
                jumped = True
                if (self._ctab is not None
                        and ntab.start - self._ctab.end == Position(0, 1)
                        and ntab.end - ntab.start == Position(0, 1)):
                    ntab_short_and_near = True
                if ntab.number == 0:
                    self.current_snippet_is_done()
            else:
                # This really shouldn't happen, because a snippet should
                # have been popped when its final tabstop was used.
                # Cleanup by removing current snippet and recursing.
                self.current_snippet_is_done()
                jumped = self.jump(backwards)
            self._ctab = ntab
        if jumped:
            self._vstate.remember_position()
            self._vstate.remember_unnamed_register(self._ctab.current_text)
            if not ntab_short_and_near:
                self._ignore_movements = True
        return jumped

    def cursor_moved(self):
        """Called whenever the cursor moved."""
        if not self._csnippets:
            self._inner_key_mapper.unmap_inner_keys()
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

        self.check_if_still_inside_snippet()
        if self._csnippets:
            self._csnippets[0].update_textobjects()
            self._vstate.remember_buffer(self._csnippets[0])

    def do_snippet(self, snippet, before):
        """Expands the given snippet, and handles everything
        that needs to be done with it."""
        self._inner_key_mapper.map_inner_keys()

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

        si.update_textobjects()

        self._ignore_movements = True
        self._vstate.remember_buffer(self._csnippets[0])

        self.jump()

    def leaving_buffer(self):
        """Called when the user switches tabs/windows/buffers. It basically
        means that all snippets must be properly terminated."""
        while len(self._csnippets):
            self.current_snippet_is_done()
        self.reinit()
