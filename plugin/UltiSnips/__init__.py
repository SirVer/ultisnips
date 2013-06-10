#!/usr/bin/env python
# encoding: utf-8

from functools import wraps
from collections import deque, defaultdict
import glob
import hashlib
import os
import re
import traceback

from UltiSnips.compatibility import as_unicode, byte2col
from UltiSnips._diff import diff, guess_edit
from UltiSnips.geometry import Position
from UltiSnips.text_objects import SnippetInstance
from UltiSnips.util import IndentUtil
import UltiSnips._vim as _vim

def err_to_scratch_buffer(f):
    @wraps(f)
    def wrapper(self, *args, **kwds):
        try:
            return f(self, *args, **kwds)
        except:
            s = \
"""An error occured. This is either a bug in UltiSnips or a bug in a
snippet definition. If you think this is a bug, please report it to
https://bugs.launchpad.net/ultisnips/+filebug.

Following is the full stack trace:
"""
            s += traceback.format_exc()
            self.leaving_buffer() # Vim sends no WinLeave msg here.
            _vim.new_scratch_buffer(s)
    return wrapper

class _SnippetDictionary(object):
    def __init__(self, *args, **kwargs):
        self._added = []
        self.reset()

    def add_snippet(self, s, fn=None):
        if fn:
            self._snippets.append(s)

            if fn not in self.files:
                self.addfile(fn)
        else:
            self._added.append(s)

    def get_matching_snippets(self, trigger, potentially):
        """Returns all snippets matching the given trigger."""
        if not potentially:
            return [ s for s in self.snippets if s.matches(trigger) ]
        else:
            return [ s for s in self.snippets if s.could_match(trigger) ]

    @property
    def snippets(self):
        return self._added + self._snippets

    def clear_snippets(self, triggers=[]):
        """Remove all snippets that match each trigger in triggers.
            When triggers is empty, removes all snippets.
        """
        if triggers:
            for t in triggers:
                for s in self.get_matching_snippets(t, potentially=False):
                    if s in self._snippets:
                        self._snippets.remove(s)
                    if s in self._added:
                        self._added.remove(s)
        else:
            self._snippets = []
            self._added = []

    @property
    def files(self):
        return self._files

    def reset(self):
        self._snippets = []
        self._extends = []
        self._files = {}


    def _hash(self, path):
        if not os.path.isfile(path):
            return False

        return hashlib.sha1(open(path, "rb").read()).hexdigest()


    def addfile(self, path):
        self.files[path] = self._hash(path)

    def needs_update(self):
        for path, hash in self.files.items():
            if not hash or hash != self._hash(path):
                return True
        return False

    def extends():
        def fget(self):
            return self._extends
        def fset(self, value):
            self._extends = value
        return locals()
    extends = property(**extends())

class _SnippetsFileParser(object):
    def __init__(self, ft, fn, snip_manager, file_data=None):
        self._sm = snip_manager
        self._ft = ft
        self._fn = fn
        self._globals = {}
        if file_data is None:
            self._lines = open(fn).readlines()
        else:
            self._lines = file_data.splitlines(True)

        self._idx = 0

    def _error(self, msg):
        fn = _vim.eval("""fnamemodify(%s, ":~:.")""" % _vim.escape(self._fn))
        self._sm._error("%s in %s(%d)" % (msg, fn, self._idx + 1))

    def _line(self):
        if self._idx < len(self._lines):
            line = self._lines[self._idx]
        else:
            line = ""
        return line

    def _line_head_tail(self):
        parts = re.split(r"\s+", self._line().rstrip(), maxsplit=1)
        parts.append('')
        return parts[:2]

    def _line_head(self):
        return self._line_head_tail()[0]

    def _line_tail(self):
        return self._line_head_tail()[1]

    def _goto_next_line(self):
        self._idx += 1
        return self._line()

    def _parse_first(self, line):
        """ Parses the first line of the snippet definition. Returns the
        snippet type, trigger, description, and options in a tuple in that
        order.
        """
        cdescr = ""
        coptions = ""
        cs = ""

        # Ensure this is a snippet
        snip = line.split()[0]

        # Get and strip options if they exist
        remain = line[len(snip):].strip()
        words = remain.split()
        if len(words) > 2:
            # second to last word ends with a quote
            if '"' not in words[-1] and words[-2][-1] == '"':
                coptions = words[-1]
                remain = remain[:-len(coptions) - 1].rstrip()

        # Get and strip description if it exists
        remain = remain.strip()
        if len(remain.split()) > 1 and remain[-1] == '"':
            left = remain[:-1].rfind('"')
            if left != -1 and left != 0:
                cdescr, remain = remain[left:], remain[:left]

        # The rest is the trigger
        cs = remain.strip()
        if len(cs.split()) > 1 or "r" in coptions:
            if cs[0] != cs[-1]:
                self._error("Invalid multiword trigger: '%s'" % cs)
                cs = ""
            else:
                cs = cs[1:-1]

        return (snip, cs, cdescr, coptions)

    def _parse_snippet(self):
        line = self._line()

        (snip, trig, desc, opts) = self._parse_first(line)
        end = "end" + snip
        cv = ""

        while self._goto_next_line():
            line = self._line()
            if line.rstrip() == end:
                cv = cv[:-1] # Chop the last newline
                break
            cv += line
        else:
            self._error("Missing 'endsnippet' for %r" % trig)
            return None

        if not trig:
            # there was an error
            return None
        elif snip == "global":
            # add snippet contents to file globals
            if trig not in self._globals:
                self._globals[trig] = []
            self._globals[trig].append(cv)
        elif snip == "snippet":
            self._sm.add_snippet(trig, cv, desc, opts, self._ft, self._globals, fn=self._fn)
        else:
            self._error("Invalid snippet type: '%s'" % snip)

    def parse(self):
        while self._line():
            head, tail = self._line_head_tail()
            if head == "extends":
                if tail:
                    self._sm.add_extending_info(self._ft,
                        [ p.strip() for p in tail.split(',') ])
                else:
                    self._error("'extends' without file types")
            elif head in ("snippet", "global"):
                self._parse_snippet()
            elif head == "clearsnippets":
                self._sm.clear_snippets(tail.split(), self._ft)
            elif head and not head.startswith('#'):
                self._error("Invalid line %r" % self._line().rstrip())
                break
            self._goto_next_line()



class Snippet(object):
    _INDENT = re.compile(r"^[ \t]*")
    _TABS = re.compile(r"^\t*")

    def __init__(self, trigger, value, descr, options, globals):
        self._t = as_unicode(trigger)
        self._v = as_unicode(value)
        self._d = as_unicode(descr)
        self._opts = options
        self._matched = ""
        self._last_re = None
        self._globals = globals

    def __repr__(self):
        return "Snippet(%s,%s,%s)" % (self._t,self._d,self._opts)

    def _words_for_line(self, before, num_words=None):
        """ Gets the final num_words words from before.
        If num_words is None, then use the number of words in
        the trigger.
        """
        words = ''
        if not len(before):
            return ''

        if num_words is None:
            num_words = len(self._t.split())

        word_list = before.split()
        if len(word_list) <= num_words:
            return before.strip()
        else:
            before_words = before
            for i in range(-1, -(num_words + 1), -1):
                left = before_words.rfind(word_list[i])
                before_words = before_words[:left]
            return before[len(before_words):].strip()

    def _re_match(self, trigger):
        """ Test if a the current regex trigger matches
        `trigger`. If so, set _last_re and _matched.
        """
        for match in re.finditer(self._t, trigger):
            if match.end() != len(trigger):
                continue
            else:
                self._matched = trigger[match.start():match.end()]

            self._last_re = match
            return match
        return False

    def has_option(self, opt):
        """ Check if the named option is set """
        return opt in self._opts

    def matches(self, trigger):
        # If user supplies both "w" and "i", it should perhaps be an
        # error, but if permitted it seems that "w" should take precedence
        # (since matching at word boundary and within a word == matching at word
        # boundary).
        self._matched = ""

        # Don't expand on whitespace
        if trigger and trigger.rstrip() != trigger:
            return False

        words = self._words_for_line(trigger)

        if "r" in self._opts:
            match = self._re_match(trigger)
        elif "w" in self._opts:
            words_len = len(self._t)
            words_prefix = words[:-words_len]
            words_suffix = words[-words_len:]
            match = (words_suffix == self._t)
            if match and words_prefix:
                # Require a word boundary between prefix and suffix.
                boundaryChars = words_prefix[-1:] + words_suffix[:1]
                match = re.match(r'.\b.', boundaryChars)
        elif "i" in self._opts:
            match = words.endswith(self._t)
        else:
            match = (words == self._t)

        # By default, we match the whole trigger
        if match and not self._matched:
            self._matched = self._t

        # Ensure the match was on a word boundry if needed
        if "b" in self._opts and match:
            text_before = trigger.rstrip()[:-len(self._matched)]
            if text_before.strip(" \t") != '':
                self._matched = ""
                return False

        return match

    def could_match(self, trigger):
        self._matched = ""

        # List all on whitespace.
        if trigger and trigger[-1] in (" ", "\t"):
            trigger = ""
        if trigger and trigger.rstrip() is not trigger:
            return False

        words = self._words_for_line(trigger)

        if "r" in self._opts:
            # Test for full match only
            match = self._re_match(trigger)
        elif "w" in self._opts:
            # Trim non-empty prefix up to word boundary, if present.
            words_suffix = re.sub(r'^.+\b(.+)$', r'\1', words)
            match = self._t.startswith(words_suffix)
            self._matched = words_suffix

            # TODO: list_snippets() function cannot handle partial-trigger
            # matches yet, so for now fail if we trimmed the prefix.
            if words_suffix != words:
                match = False
        elif "i" in self._opts:
            # TODO: It is hard to define when a inword snippet could match,
            # therefore we check only for full-word trigger.
            match = self._t.startswith(words)
        else:
            match = self._t.startswith(words)

        # By default, we match the words from the trigger
        if match and not self._matched:
            self._matched = words

        # Ensure the match was on a word boundry if needed
        if "b" in self._opts and match:
            text_before = trigger.rstrip()[:-len(self._matched)]
            if text_before.strip(" \t") != '':
                self._matched = ""
                return False

        return match

    @property
    def overwrites_previous(self):
        return "!" in self._opts

    @property
    def description(self):
        return ("(%s) %s" % (self._t, self._d)).strip()

    @property
    def trigger(self):
        return self._t

    @property
    def matched(self):
        """ The last text that was matched. """
        return self._matched

    def launch(self, text_before, visual_content, parent, start, end):
        indent = self._INDENT.match(text_before).group(0)
        lines = (self._v + "\n").splitlines()
        ind_util = IndentUtil()

        # Replace leading tabs in the snippet definition via proper indenting
        v = []
        for line_num, line in enumerate(lines):
            if "t" in self._opts:
                tabs = 0
            else:
                tabs = len(self._TABS.match(line).group(0))

            line_ind = ind_util.ntabs_to_proper_indent(tabs)

            if line_num != 0:
                line_ind = indent + line_ind

            v.append(line_ind + line[tabs:])
        v = '\n'.join(v)

        si = SnippetInstance(self, parent, indent, v, start, end, visual_content,
                last_re = self._last_re, globals = self._globals)

        return si

class VisualContentPreserver(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._mode = ""
        self._text = as_unicode("")

    def conserve(self):
        sl, sbyte = map(int, (_vim.eval("""line("'<")"""), _vim.eval("""col("'<")""")))
        el, ebyte = map(int, (_vim.eval("""line("'>")"""), _vim.eval("""col("'>")""")))
        sc = byte2col(sl, sbyte - 1)
        ec = byte2col(el, ebyte - 1)
        self._mode = _vim.eval("visualmode()")

        def _vim_line_with_eol(ln):
            return _vim.buf[ln] + '\n'

        if sl == el:
            text = _vim_line_with_eol(sl-1)[sc:ec+1]
        else:
            text = _vim_line_with_eol(sl-1)[sc:]
            for cl in range(sl,el-1):
                text += _vim_line_with_eol(cl)
            text += _vim_line_with_eol(el-1)[:ec+1]

        self._text = text

    @property
    def text(self):
        return self._text

    @property
    def mode(self):
        return self._mode

class _VimPosition(Position):
    def __init__(self):
        pos = _vim.buf.cursor
        self._mode = _vim.eval("mode()")
        self._visualmode = _vim.eval("visualmode()")
        Position.__init__(self, pos.line, pos.col)

    @property
    def mode(self):
        return self._mode
    @property
    def visualmode(self):
        return self._visualmode


class VimState(object):
    def __init__(self):
        """
        This class caches some state information from Vim to better
        guess what editing tasks the user might have done in the last step
        """
        self._poss = deque(maxlen=5)
        self._lvb = None

    def remember_position(self):
        self._poss.append(_VimPosition())

    def remember_buffer(self, to):
        self._lvb = _vim.buf[to.start.line:to.end.line+1]
        self._lvb_len = len(_vim.buf)
        self.remember_position()

    @property
    def diff_in_buffer_length(self):
        return len(_vim.buf) - self._lvb_len

    @property
    def pos(self):
        return self._poss[-1]
    @property
    def ppos(self):
        return self._poss[-2]
    @property
    def remembered_buffer(self):
        return self._lvb[:]


class SnippetManager(object):
    def __init__(self):
        self._supertab_keys = None
        self._csnippets = []

        self.reset()

    @err_to_scratch_buffer
    def reset(self, test_error=False):
        self._vstate = VimState()
        self._test_error = test_error
        self._snippets = {}
        self._filetypes = defaultdict(lambda: ['all'])
        self._visual_content = VisualContentPreserver()

        while len(self._csnippets):
            self._current_snippet_is_done()

        self._reinit()

    @err_to_scratch_buffer
    def jump_forwards(self):
        _vim.command("let g:ulti_jump_forwards_res = 1")
        if not self._jump():
            _vim.command("let g:ulti_jump_forwards_res = 0")
            return self._handle_failure(self.forward_trigger)

    @err_to_scratch_buffer
    def jump_backwards(self):
        _vim.command("let g:ulti_jump_backwards_res = 1")
        if not self._jump(True):
            _vim.command("let g:ulti_jump_backwards_res = 0")
            return self._handle_failure(self.backward_trigger)

    @err_to_scratch_buffer
    def expand(self):
        _vim.command("let g:ulti_expand_res = 1")
        if not self._try_expand():
            _vim.command("let g:ulti_expand_res = 0")
            self._handle_failure(self.expand_trigger)

    @err_to_scratch_buffer
    def list_snippets_dict(self):
        before, after = _vim.buf.current_line_splitted
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
              if description[0] == description[-1] and description[0] in ['"', "'"]:
                description = description[1:-1]

            _vim.command(as_unicode("let g:current_ulti_dict['{key}'] = '{val}'").format(
              key=key.replace("'", "''"), val=description))

    @err_to_scratch_buffer
    def list_snippets(self):
        before, after = _vim.buf.current_line_splitted
        snippets = self._snips(before, True)

        # Sort snippets alphabetically
        snippets.sort(key=lambda x: x.trigger)

        if not snippets:
            return True

        snippet = self._ask_snippets(snippets)
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

    def snippet_dict(self, ft):
        if ft not in self._snippets:
            self._snippets[ft] = _SnippetDictionary()
        return self._snippets[ft]

    @err_to_scratch_buffer
    def add_snippet(self, trigger, value, descr, options, ft = "all", globals = None, fn=None):
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
                            _vim.text_to_vim(Position(lineno,0), Position(
                                lineno,len(before)+len(after)), m.group(1))
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
            self._vstate.remember_position()
        return jumped

    def _handle_failure(self, trigger):
        """
        Mainly make sure that we play well with SuperTab
        """
        if trigger.lower() == "<tab>":
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
                self._supertab_keys = [ '', '' ]

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

    def _ask_snippets(self, snippets):
        """ Given a list of snippets, ask the user which one they
        want to use, and return it.
        """
        # make a python list
        display = [ as_unicode("%i: %s") % (i+1,s.description) for i,s in enumerate(snippets)]

        try:
            rv = _vim.eval("inputlist(%s)" % _vim.escape(display))
            if rv is None or rv == '0':
                return None
            rv = int(rv)
            if rv > len(snippets):
                rv = len(snippets)
            return snippets[rv-1]
        except _vim.error as e:
            # Likely "invalid expression", but might be translated. We have no way
            # of knowing the exact error, therefore, we ignore all errors silently.
            return None

    def _do_snippet(self, snippet, before, after):
        """ Expands the given snippet, and handles everything
        that needs to be done with it.
        """
        # Adjust before, maybe the trigger is not the complete word
        text_before = before
        if snippet.matched:
            text_before = before[:-len(snippet.matched)]

        if self._cs:
            start = Position(_vim.buf.cursor.line, len(text_before))
            end = Position(_vim.buf.cursor.line, len(before))

            si = snippet.launch(text_before, self._visual_content,
                    self._cs.find_parent_for_new_to(start), start, end)
        else:
            start = Position(_vim.buf.cursor.line, len(text_before))
            end = Position(_vim.buf.cursor.line, len(before))
            si = snippet.launch(text_before, self._visual_content, None, start, end)

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
            snippet = self._ask_snippets(snippets)
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
        _SnippetsFileParser(ft, fn, self, file_data).parse()

    def base_snippet_files_for(self, ft, default=True):
        """ Returns a list of snippet files matching the given filetype (ft).
        If default is set to false, it doesn't include shipped files.

        Searches through each path in 'runtimepath' in reverse order,
        in each of these, it searches each directory name listed in
        'g:UltiSnipsSnippetDirectories' in order, then looks for files in these
        directories called 'ft.snippets' or '*_ft.snippets' replacing ft with
        the filetype.
        """

        snippet_dirs = _vim.eval("g:UltiSnipsSnippetDirectories")
        base_snippets = os.path.realpath(os.path.join(__file__, "../../../UltiSnips"))
        ret = []

        paths = _vim.eval("&runtimepath").split(',')

        if _vim.eval("exists('g:UltiSnipsDontReverseSearchPath')") == "0" or \
           _vim.eval("g:UltiSnipsDontReverseSearchPath") == "0":
            paths = paths[::-1]

        for rtp in paths:
            for snippet_dir in snippet_dirs:
                pth = os.path.realpath(os.path.expanduser(os.path.join(rtp, snippet_dir)))

                patterns = ["%s.snippets", "%s_*.snippets", os.path.join("%s","*")]
                if not default and pth == base_snippets:
                    patterns.remove("%s.snippets")

                for pattern in patterns:
                    for fn in glob.glob(os.path.join(pth, pattern % ft)):
                        if fn not in ret:
                            ret.append(fn)

        return ret

    @property
    def primary_filetype(self):
        """ Property for the primary filetype. This filetype
        will be edited when UltiSnipsEdit is called
        without any arguments.
        """
        return self._filetypes[_vim.buf.nr][0]

    def file_to_edit(self, ft):
        """ Gets a file to edit based on the given filetype.
        If no filetype is given, uses the current filetype from Vim.

        Checks 'g:UltiSnipsSnippetsDir' and uses it if it exists
        If a non-shipped file already exists, it uses it.
        Otherwise uses a file in ~/.vim/ or ~/vimfiles
        """
        edit = None
        existing = self.base_snippet_files_for(ft, False)
        filename = ft + ".snippets"

        if _vim.eval("exists('g:UltiSnipsSnippetsDir')") == "1":
            snipdir = _vim.eval("g:UltiSnipsSnippetsDir")
            edit = os.path.join(snipdir, filename)
        elif existing:
            edit = existing[-1] # last sourced/highest priority
        else:
            home = _vim.eval("$HOME")
            rtp = [ os.path.realpath(os.path.expanduser(p)) for p in _vim.eval("&rtp").split(",") ]
            snippet_dirs = ["UltiSnips"] + _vim.eval("g:UltiSnipsSnippetDirectories")
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

    # Loading
    def _load_snippets_for(self, ft):
        self.snippet_dict(ft).reset()

        for fn in self.base_snippet_files_for(ft):
            self._parse_snippets(ft, fn)

        # Now load for the parents
        for p in self._snippets[ft].extends:
            if p not in self._snippets:
                self._load_snippets_for(p)


    def _needs_update(self, ft):
        do_hash = _vim.eval('exists("g:UltiSnipsDoHash")') == "0" \
                or _vim.eval("g:UltiSnipsDoHash") != "0"

        if ft not in self._snippets:
            return True
        elif do_hash and self.snippet_dict(ft).needs_update():
            return True
        elif do_hash:
            cur_snips = set(self.base_snippet_files_for(ft))
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
        snips = self._snippets.get(ft,None)
        if not snips:
            return []

        if not seen:
            seen = []
        seen.append(ft)

        parent_results = []

        for p in snips.extends:
            if p not in seen:
                seen.append(p)
                parent_results += self._find_snippets(p, trigger,
                        potentially, seen)

        return parent_results + snips.get_matching_snippets(
            trigger, potentially)


UltiSnips_Manager = SnippetManager()

