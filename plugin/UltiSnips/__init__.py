#!/usr/bin/env python
# encoding: utf-8

"""Contains the SnippetManager facade used by all Vim Functions."""

from collections import defaultdict
from functools import wraps
import glob
import os
import re
import traceback

from UltiSnips._diff import diff, guess_edit
from UltiSnips.compatibility import as_unicode
from UltiSnips.geometry import Position
from UltiSnips.snippet import Snippet
from UltiSnips.snippet_dictionary import SnippetDictionary
from UltiSnips.snippets_file_parser import SnippetsFileParser
from UltiSnips.vim_state import VimState
from UltiSnips.visual_content_preserver import VisualContentPreserver
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

def _base_snippet_files_for(ft, default=True):
    """ Returns a list of snippet files matching the given filetype (ft).
    If default is set to false, it doesn't include shipped files.

    Searches through each path in 'runtimepath' in reverse order,
    in each of these, it searches each directory name listed in
    'g:UltiSnipsSnippetDirectories' in order, then looks for files in these
    directories called 'ft.snippets' or '*_ft.snippets' replacing ft with
    the filetype.
    """

    if _vim.eval("exists('b:UltiSnipsSnippetDirectories')") == "1":
        snippet_dirs = _vim.eval("b:UltiSnipsSnippetDirectories")
    else:
        snippet_dirs = _vim.eval("g:UltiSnipsSnippetDirectories")
    base_snippets = os.path.realpath(os.path.join(
        __file__, "../../../UltiSnips"))
    ret = []

    paths = _vim.eval("&runtimepath").split(',')

    if _should_reverse_search_path():
        paths = paths[::-1]

    for rtp in paths:
        for snippet_dir in snippet_dirs:
            pth = os.path.realpath(os.path.expanduser(
                os.path.join(rtp, snippet_dir)))
            patterns = ["%s.snippets", "%s_*.snippets", os.path.join("%s", "*")]
            if not default and pth == base_snippets:
                patterns.remove("%s.snippets")

            for pattern in patterns:
                for fn in glob.glob(os.path.join(pth, pattern % ft)):
                    if fn not in ret:
                        ret.append(fn)

    return ret


def _plugin_dir():
    """ Calculates the plugin directory for UltiSnips. This depends on the
    current file being 3 levels deep from the plugin directory, so it needs to
    be updated if the code moves.
    """
    directory = __file__
    for _ in range(10):
        directory = os.path.dirname(directory)
        if (os.path.isdir(os.path.join(directory, "plugin")) and
            os.path.isdir(os.path.join(directory, "doc"))):
            return directory
    raise Exception("Unable to find the plugin directory.")

def _snippets_dir_is_before_plugin_dir():
    """ Returns True if the snippets directory comes before the plugin
    directory in Vim's runtime path. False otherwise.
    """
    paths = [os.path.realpath(os.path.expanduser(p)).rstrip(os.path.sep)
        for p in _vim.eval("&runtimepath").split(',')]
    home = _vim.eval("$HOME")
    def vim_path_index(suffix):
        """Returns index of 'suffix' in 'paths' or -1 if it is not found."""
        path = os.path.realpath(os.path.join(home, suffix)).rstrip(os.path.sep)
        try:
            return paths.index(path)
        except ValueError:
            return -1
    try:
        real_vim_path_index = max(
                vim_path_index(".vim"), vim_path_index("vimfiles"))
        plugin_path_index = paths.index(_plugin_dir())
        return plugin_path_index < real_vim_path_index
    except ValueError:
        return False

def _should_reverse_search_path():
    """ If the user defined g:UltiSnipsDontReverseSearchPath then return True
    or False based on the value of that variable, else defer to
    _snippets_dir_is_before_plugin_dir to determine whether this is True or
    False.
    """
    if _vim.eval("exists('g:UltiSnipsDontReverseSearchPath')") != "0":
        return _vim.eval("g:UltiSnipsDontReverseSearchPath") != "0"
    return not _snippets_dir_is_before_plugin_dir()

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
https://bugs.launchpad.net/ultisnips/+filebug.

Following is the full stack trace:
"""
            msg += traceback.format_exc()
            self.leaving_buffer() # Vim sends no WinLeave msg here.
            _vim.new_scratch_buffer(msg)
    return wrapper

class SnippetManager(object):
    def __init__(self, expand_trigger, forward_trigger, backward_trigger):
        """The main entry point for all UltiSnips functionality. All Vim
        functions call methods in this class."""
        self.expand_trigger = expand_trigger
        self.forward_trigger = forward_trigger
        self.backward_trigger = backward_trigger
        self._supertab_keys = None
        self._csnippets = []

        self.reset()

    @err_to_scratch_buffer
    def reset(self, test_error=False):
        """Reset the class to the state it had directly after creation."""
        self._vstate = VimState()
        self._test_error = test_error
        self._snippets = {}
        self._filetypes = defaultdict(lambda: ['all'])
        self._visual_content = VisualContentPreserver()

        while len(self._csnippets):
            self._current_snippet_is_done()

        # needed to retain the unnamed register at all times
        self._unnamed_reg_cached = False
        self._last_placeholder = None

        self._reinit()

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
        """Trie to expand a snippet at the current position."""
        _vim.command("let g:ulti_expand_res = 1")
        if not self._try_expand():
            _vim.command("let g:ulti_expand_res = 0")
            self._handle_failure(self.expand_trigger)

    @err_to_scratch_buffer
    def snippets_in_current_scope(self):
        """Returns the snippets that could be expanded to Vim as a global
        variable."""
        before, _ = _vim.buf.current_line_splitted
        snippets = self._snips(before, True)

        # Sort snippets alphabetically
        snippets.sort(key=lambda x: x.trigger)
        for snip in snippets:
            description = snip.description[snip.description.find(snip.trigger) +
                len(snip.trigger) + 2:]

            key = as_unicode(snip.trigger)
            description = as_unicode(description)

            #remove surrounding "" or '' in snippet description if it exists
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
        before, after = _vim.buf.current_line_splitted
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

        self._do_snippet(snippet, before, after)

        return True

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
    def save_last_visual_selection(self):
        """
        This is called when the expand trigger is pressed in visual mode.
        Our job is to remember everything between '< and '> and pass it on to
        ${VISUAL} in case it will be needed.
        """
        self._visual_content.conserve()

    # TODO(sirver): replace through defaultdict
    def snippet_dict(self, ft):
        """Makes sure that ft is in self._snippets."""
        if ft not in self._snippets:
            self._snippets[ft] = SnippetDictionary()
        return self._snippets[ft]

    @err_to_scratch_buffer
    def add_snippet(self, trigger, value, descr, options, ft="all", globals=None, fn=None):
        """Add a snippet to the list of known snippets of the given 'ft'."""
        l = self.snippet_dict(ft).add_snippet(
            Snippet(trigger, value, descr, options, globals or {}), fn
        )

    @err_to_scratch_buffer
    def add_snippet_file(self, ft, path):
        sd = self.snippet_dict(ft)
        sd.addfile(path)

    @err_to_scratch_buffer
    def expand_anon(self, value, trigger="", descr="", options="", globals=None):
        if globals is None:
            globals = {}

        before, after = _vim.buf.current_line_splitted
        snip = Snippet(trigger, value, descr, options, globals)

        if not trigger or snip.matches(before):
            self._do_snippet(snip, before, after)
            return True
        else:
            return False

    @err_to_scratch_buffer
    def clear_snippets(self, triggers = [], ft = "all"):
        if ft in self._snippets:
            self._snippets[ft].clear_snippets(triggers)

    @err_to_scratch_buffer
    def add_extending_info(self, ft, parents):
        sd = self.snippet_dict(ft)
        for p in parents:
            if p in sd.extends:
                continue

            sd.extends.append(p)

    @err_to_scratch_buffer
    def cursor_moved(self):
        self._vstate.remember_position()
        if _vim.eval("mode()") not in 'in':
            return

        if self._ignore_movements:
            self._ignore_movements = False
            return

        if self._csnippets:
            cstart = self._csnippets[0].start.line
            cend = self._csnippets[0].end.line + self._vstate.diff_in_buffer_length
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
                        self._vstate.ppos.line < initial_line + lt_span[1]-1 and pos.line < initial_line + ct_span[1]-1 and
                       (lt_span[0] < lt_span[1]) and
                       (ct_span[0] < ct_span[1])):
                    ct_span[1] -= 1
                    lt_span[1] -= 1
                while (lt_span[0] < lt_span[1] and
                       ct_span[0] < ct_span[1] and
                       lt[lt_span[0]] == ct[ct_span[0]] and
                       self._vstate.ppos.line >= initial_line and pos.line >= initial_line):
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
                pass # Rather do nothing than throwing an error. It will be correct most of the time

        self._check_if_still_inside_snippet()
        if self._csnippets:
            self._csnippets[0].update_textobjects()
            self._vstate.remember_buffer(self._csnippets[0])

    def leaving_buffer(self):
        """
        Called when the user switches tabs/windows/buffers. It basically means
        that all snippets must be properly terminated
        """
        while len(self._csnippets):
            self._current_snippet_is_done()
        self._reinit()


    ###################################
    # Private/Protect Functions Below #
    ###################################
    def _error(self, msg):
        msg = _vim.escape("UltiSnips: " + msg)
        if self._test_error:
            msg = msg.replace('"', r'\"')
            msg = msg.replace('|', r'\|')
            _vim.command("let saved_pos=getpos('.')")
            _vim.command("$:put =%s" % msg)
            _vim.command("call setpos('.', saved_pos)")
        elif False:
            _vim.command("echohl WarningMsg")
            _vim.command("echomsg %s" % msg)
            _vim.command("echohl None")
        else:
            _vim.command("echoerr %s" % msg)

    def _reinit(self):
        self._ctab = None
        self._ignore_movements = False

    def _check_if_still_inside_snippet(self):
        # Did we leave the snippet with this movement?
        if self._cs and (
            not self._cs.start <= _vim.buf.cursor <= self._cs.end
        ):
            self._current_snippet_is_done()
            self._reinit()
            self._check_if_still_inside_snippet()

    def _current_snippet_is_done(self):
        self._csnippets.pop()
        if not self._csnippets and _vim.eval("g:UltiSnipsClearJumpTrigger") != "0":
            _vim.command("call UltiSnips_RestoreInnerKeys()")

    def _jump(self, backwards = False):
        jumped = False
        if self._cs:
            self._ctab = self._cs.select_next_tab(backwards)
            if self._ctab:
                before, after = _vim.buf.current_line_splitted
                if self._cs.snippet.has_option("s"):
                    if after == "":
                        m = re.match(r'(.*?)\s+$', before)
                        if m:
                            lineno = _vim.buf.cursor.line
                            _vim.text_to_vim(Position(lineno, 0), Position(
                                lineno, len(before)+len(after)), m.group(1))
                _vim.select(self._ctab.start, self._ctab.end)
                jumped = True
                if self._ctab.no == 0:
                    self._current_snippet_is_done()
            else:
                # This really shouldn't happen, because a snippet should
                # have been popped when its final tabstop was used.
                # Cleanup by removing current snippet and recursing.
                self._current_snippet_is_done()
                jumped = self._jump(backwards)
        if jumped:
            self._cache_unnamed_register()
            self._vstate.remember_position()
            self._ignore_movements = True
        return jumped

    def _cache_unnamed_register(self):
        self._unnamed_reg_cached = True
        unnamed_reg = _vim.eval('@"')
        if self._last_placeholder != unnamed_reg:
          self._unnamed_reg_cache = unnamed_reg
        self._last_placeholder = self._ctab._initial_text

    def restore_unnamed_register(self):
        if self._unnamed_reg_cached:
            escaped_cache = self._unnamed_reg_cache.replace("'", "''")
            _vim.command("let @\"='%s'" % escaped_cache)
            self._unnamed_register_cached = False

    def _handle_failure(self, trigger):
        """
        Mainly make sure that we play well with SuperTab
        """
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
                    feedkey= r"\<Plug>SuperTabForward"
                    mode = "n"
                elif idx == 1:
                    feedkey = r"\<Plug>SuperTabBackward"
                    mode = "p"
                # Use remap mode so SuperTab mappings will be invoked.
                break

        if feedkey == r"\<Plug>SuperTabForward" or feedkey == r"\<Plug>SuperTabBackward":
            _vim.command("return SuperTab(%s)" % _vim.escape(mode))
        elif feedkey:
            _vim.command("return %s" % _vim.escape(feedkey))

    def _snips(self, before, possible):
        """ Returns all the snippets for the given text
        before the cursor. If possible is True, then get all
        possible matches.
        """
        self._ensure_all_loaded()
        filetypes = self._filetypes[_vim.buf.nr][::-1]

        found_snippets = []
        for ft in filetypes:
            found_snippets += self._find_snippets(ft, before, possible)

        # Search if any of the snippets overwrites the previous
        # Dictionary allows O(1) access for easy overwrites
        snippets = {}
        for s in found_snippets:
            if (s.trigger not in snippets) or s.overwrites_previous:
                snippets[s.trigger] = []
            snippets[s.trigger].append(s)

        # Transform dictionary into flat list of snippets
        selected_snippets = set([item for sublist in snippets.values() for item in sublist])
        # Return snippets to their original order
        snippets = [snip for snip in found_snippets if snip in selected_snippets]

        return snippets

    def _do_snippet(self, snippet, before, after):
        """ Expands the given snippet, and handles everything
        that needs to be done with it.
        """
        if _vim.eval("g:UltiSnipsClearJumpTrigger") == "1":
           _vim.command("call UltiSnips_MapInnerKeys()")
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
        before, after = _vim.buf.current_line_splitted
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
        self._do_snippet(snippet, before, after)
        return True

    @property
    def _cs(self):
        if not len(self._csnippets):
            return None
        return self._csnippets[-1]

    def _parse_snippets(self, ft, fn, file_data=None):
        self.add_snippet_file(ft, fn)
        SnippetsFileParser(ft, fn, self, file_data).parse()

    @property
    def primary_filetype(self):
        """ This filetype will be edited when UltiSnipsEdit is called without
        any arguments.
        """
        return self._filetypes[_vim.buf.nr][0]

    def file_to_edit(self, ft):
        """ Gets a file to edit based on the given filetype.
        If no filetype is given, uses the current filetype from Vim.

        Checks 'g:UltiSnipsSnippetsDir' and uses it if it exists
        If a non-shipped file already exists, it uses it.
        Otherwise uses a file in ~/.vim/ or ~/vimfiles
        """
        # This method is not using self, but is called by UltiSnips.vim and is
        # therefore in this class because it is the facade to Vim.
        edit = None
        existing = _base_snippet_files_for(ft, False)
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

    def _load_snippets_for(self, ft):
        self.snippet_dict(ft).reset()
        for fn in _base_snippet_files_for(ft):
            self._parse_snippets(ft, fn)
        # Now load for the parents
        for parent_ft in self._snippets[ft].extends:
            if parent_ft not in self._snippets:
                self._load_snippets_for(parent_ft)

    def _needs_update(self, ft):
        do_hash = _vim.eval('exists("g:UltiSnipsDoHash")') == "0" \
                or _vim.eval("g:UltiSnipsDoHash") != "0"

        if ft not in self._snippets:
            return True
        elif do_hash and self.snippet_dict(ft).needs_update():
            return True
        elif do_hash:
            cur_snips = set(_base_snippet_files_for(ft))
            old_snips = set(self.snippet_dict(ft).files)
            if cur_snips - old_snips:
                return True
        return False

    def _ensure_loaded(self, ft, checked=None):
        if not checked:
            checked = set([ft])
        elif ft in checked:
            return
        else:
            checked.add(ft)

        if self._needs_update(ft):
            self._load_snippets_for(ft)

        for parent in self.snippet_dict(ft).extends:
            self._ensure_loaded(parent, checked)

    def _ensure_all_loaded(self):
        for ft in self._filetypes[_vim.buf.nr]:
            self._ensure_loaded(ft)

    def reset_buffer_filetypes(self):
        if _vim.buf.nr in self._filetypes:
            del self._filetypes[_vim.buf.nr]

    def add_buffer_filetypes(self, ft):
        """ Checks for changes in the list of snippet files or the contents
        of the snippet files and reloads them if necessary.
        """
        buf_fts = self._filetypes[_vim.buf.nr]
        idx = -1
        for ft in ft.split("."):
            ft = ft.strip()
            if not ft: continue
            try:
                idx = buf_fts.index(ft)
            except ValueError:
                self._filetypes[_vim.buf.nr].insert(idx + 1, ft)
                idx += 1
        self._ensure_all_loaded()

    def _find_snippets(self, ft, trigger, potentially = False, seen=None):
        """
        Find snippets matching trigger

        ft          - file type to search
        trigger     - trigger to match against
        potentially - also returns snippets that could potentially match; that
                      is which triggers start with the current trigger
        """
        snips = self._snippets.get(ft, None)
        if not snips:
            return []
        if not seen:
            seen = []
        seen.append(ft)
        parent_results = []
        for parent_ft in snips.extends:
            if parent_ft not in seen:
                seen.append(parent_ft)
                parent_results += self._find_snippets(parent_ft, trigger,
                        potentially, seen)
        return parent_results + snips.get_matching_snippets(
            trigger, potentially)
