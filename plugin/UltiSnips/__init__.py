#!/usr/bin/env python
# encoding: utf-8

import glob
import os
import re
import string
import vim

from UltiSnips.Geometry import Position
from UltiSnips.TextObjects import *
from UltiSnips.Buffer import VimBuffer

# The following lines silence DeprecationWarnings. They are raised
# by python2.6 for vim.error (which is a string that is used as an exception,
# which is deprecated since 2.5 and will no longer work in 2.7. Let's hope
# vim gets this fixed before)
import sys
if sys.version_info[:2] >= (2,6):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

def _vim_quote(s):
    """Quote string s as Vim literal string."""
    return "'" + s.replace("'", "''") + "'"

def feedkeys(s, mode='n'):
    """Wrapper around vim's feedkeys function. Mainly for convenience."""
    vim.command(r'call feedkeys("%s", "%s")' % (s, mode))

class _SnippetDictionary(object):
    def __init__(self, *args, **kwargs):
        self._snippets = []
        self._extends = []

    def add_snippet(self, s):
        self._snippets.append(s)

    def get_matching_snippets(self, trigger, potentially):
        """Returns all snippets matching the given trigger."""
        if not potentially:
            return [ s for s in self._snippets if s.matches(trigger) ]
        else:
            return [ s for s in self._snippets if s.could_match(trigger) ]

    def clear_snippets(self, triggers=[]):
        """Remove all snippets that match each trigger in triggers.
            When triggers is empty, removes all snippets.
        """
        if triggers:
            for t in triggers:
                for s in self.get_matching_snippets(t, potentially=False):
                    self._snippets.remove(s)
        else:
            self._snippets = []

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
        fn = vim.eval("""fnamemodify(%s, ":~:.")""" % _vim_quote(self._fn))
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
        remain = line[len(snip):].lstrip()
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
            self._sm.add_snippet(trig, cv, desc, opts, self._ft, self._globals)
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

    def __init__(self, trigger, value, descr, options, globals):
        self._t = trigger
        self._v = value
        self._d = descr
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
            for i in xrange(-1, -(num_words + 1), -1):
                left = before_words.rfind(word_list[i])
                before_words = before_words[:left]
            return before[len(before_words):].strip()

    def _re_match(self, trigger):
        """ Test if a the current regex trigger matches
        `trigger`. If so, set _last_re and _matched.
        """
        match = re.search(self._t, trigger)
        if match:
            if match.end() != len(trigger):
                match = False
            else:
                self._matched = trigger[match.start():match.end()]
        if match:
            self._last_re = match
        else:
            self._last_re = None
        return match

    def matches(self, trigger):
        # If user supplies both "w" and "i", it should perhaps be an
        # error, but if permitted it seems that "w" should take precedence
        # (since matching at word boundary and within a word == matching at word
        # boundary).
        self._matched = ""

        # Don't expand on whitespace
        if trigger and trigger[-1] in string.whitespace:
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

        # Don't expand on whitespace
        if trigger and trigger[-1] in string.whitespace:
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

    def overwrites_previous(self):
        return "!" in self._opts
    overwrites_previous = property(overwrites_previous)

    def description(self):
        return ("(%s) %s" % (self._t, self._d)).strip()
    description = property(description)

    def trigger(self):
        return self._t
    trigger = property(trigger)

    def matched(self):
        """ The last text that was matched. """
        return self._matched
    matched = property(matched)

    def launch(self, text_before, parent, start, end = None):
        indent = self._INDENT.match(text_before).group(0)
        v = self._v
        if len(indent):
            lines = self._v.splitlines()
            v = lines[0]
            if len(lines) > 1:
                v += os.linesep + \
                        os.linesep.join([indent + l for l in lines[1:]])

        if vim.eval("&expandtab") == '1':
            ts = int(vim.eval("&ts"))
            # expandtabs will not work for us, we have to replace all tabstops
            # so that indent is right at least. tabs in the middle of the line
            # will not be expanded correctly
            v = v.replace('\t', ts*" ")

        if parent is None:
            return SnippetInstance(StartMarker(start), indent,
                    v, last_re = self._last_re, globals = self._globals)
        else:
            return SnippetInstance(parent, indent, v, start,
                    end, last_re = self._last_re, globals = self._globals)

class LangMapTranslator(object):
    """
    This object cares for the vim langmap option and basically reverses
    the mappings. This was the only solution to get UltiSnips to work
    nicely with langmap; other stuff I tried was using inoremap movement
    commands and caching and restoring the langmap option.

    Note that this will not work if the langmap overwrites a character
    completely, for example if 'j' is remapped, but nothing is mapped
    back to 'j', then moving one line down is no longer possible and
    UltiSnips will fail.
    """
    _maps = {}

    def _create_translation(self, langmap):
        from_chars, to_chars = "", ""
        for c in langmap.split(','):
            if ";" in c:
                a,b = c.split(';')
                from_chars += a
                to_chars += b
            else:
                from_chars += c[::2]
                to_chars += c[1::2]

        self._maps[langmap] = string.maketrans(to_chars, from_chars)

    def translate(self, s):
        langmap = vim.eval("&langmap").strip()
        if langmap == "":
            return s

        if langmap not in self._maps:
            self._create_translation(langmap)

        return s.translate(self._maps[langmap])

class VimState(object):
    def __init__(self):
        self._abs_pos = None
        self._moved = Position(0,0)

        self._lines = None
        self._dlines = None
        self._cols = None
        self._dcols = None
        self._cline = None
        self._lline = None
        self._text_changed = None

    def update(self):
        line, col = vim.current.window.cursor
        line -= 1
        abs_pos = Position(line,col)
        if self._abs_pos:
            self._moved = abs_pos - self._abs_pos
        self._abs_pos = abs_pos

        # Update buffer infos
        cols = len(vim.current.buffer[line])
        if self._cols:
            self._dcols = cols - self._cols
        self._cols = cols

        lines = len(vim.current.buffer)
        if self._lines:
            self._dlines = lines - self._lines
        self._lines = lines

        # Check if the buffer has changed in any ways
        self._text_changed = False
        # does it have more lines?
        if self._dlines:
            self._text_changed = True
        # did we stay in the same line and it has more columns now?
        elif not self.moved.line and self._dcols:
            self._text_changed = True
        # If the length didn't change but we moved a column, check if
        # the char under the cursor has changed (might be one char tab).
        elif self.moved.col == 1:
            self._text_changed = self._cline != vim.current.buffer[line]
        self._lline = self._cline
        self._cline = vim.current.buffer[line]

    def select_span(self, r):
        self._unmap_select_mode_mapping()

        delta = r.end - r.start
        lineno, col = r.start.line, r.start.col

        vim.current.window.cursor = lineno + 1, col

        if delta.line == delta.col == 0:
            if col == 0 or vim.eval("mode()") != 'i':
                feedkeys(r"\<Esc>i")
            else:
                feedkeys(r"\<Esc>a")
        else:
            # If a tabstop immediately starts with a newline, the selection
            # must start after the last character in the current line. But if
            # we are in insert mode and <Esc> out of it, we cannot go past the
            # last character with move_one_right and therefore cannot
            # visual-select this newline. We have to hack around this by adding
            # an extra space which we can select.  Note that this problem could
            # be circumvent by selecting the tab backwards (that is starting
            # at the end); one would not need to modify the line for this.
            if col >= len(vim.current.buffer[lineno]):
                vim.current.buffer[lineno] += " "

            if delta.line:
                move_lines = "%ij" % delta.line
            else:
                move_lines = ""
            # Depending on the current mode and position, we
            # might need to move escape out of the mode and this
            # will move our cursor one left
            if col != 0 and vim.eval("mode()") == 'i':
                move_one_right = "l"
            else:
                move_one_right = ""

            # After moving to the correct line, we go back to column 0
            # and select right from there. Note that the we have to select
            # one column less since vim's visual selection is including the
            # ending while Python slicing is excluding the ending.
            if r.end.col == 0 and not len(vim.current.buffer[r.end.line]):
                # Selecting should end on an empty line -> Select the previous
                # line till its end
                do_select = "k$"
            elif r.end.col > 1:
                do_select = "0%il" % (r.end.col-1)
            else:
                do_select = "0"

            move_cmd = LangMapTranslator().translate(
                r"\<Esc>%sv%s%s\<c-g>" % (move_one_right, move_lines, do_select)
            )

            feedkeys(move_cmd)


    def buf_changed(self):
        return self._text_changed
    buf_changed = property(buf_changed)

    def pos(self):
        return self._abs_pos
    pos = property(pos)

    def ppos(self):
        if not self.has_moved:
            return self.pos
        return self.pos - self.moved
    ppos = property(ppos)

    def moved(self):
        return self._moved
    moved = property(moved)

    def has_moved(self):
        return bool(self._moved.line or self._moved.col)
    has_moved = property(has_moved)

    def last_line(self):
        return self._lline
    last_line = property(last_line)

    ###########################
    # Private functions below #
    ###########################
    def _unmap_select_mode_mapping(self):
        """This function unmaps select mode mappings if so wished by the user.
        Removes select mode mappings that can actually be typed by the user
        (ie, ignores things like <Plug>).
        """
        if int(vim.eval("g:UltiSnipsRemoveSelectModeMappings")):
            ignores = vim.eval("g:UltiSnipsMappingsToIgnore") + ['UltiSnips']

            for option in ("<buffer>", ""):
                # Put all smaps into a var, and then read the var
                vim.command(r"redir => _tmp_smaps | silent smap %s " % option +
                            "| redir END")

                # Check if any mappings where found
                all_maps = filter(len, vim.eval(r"_tmp_smaps").splitlines())
                if (len(all_maps) == 1 and
                    all_maps[0][0] not in " sv"):
                        # "No maps found". String could be localized. Hopefully
                        # it doesn't start with any of these letters in any
                        # language
                        continue

                # Only keep mappings that should not be ignored
                maps = [m for m in all_maps if
                            not any(i in m for i in ignores) and len(m.strip())]

                for m in maps:
                    # Some mappings have their modes listed
                    trig = m.split()
                    if m[0] == " ":
                        trig = trig[0]
                    else:
                        trig = trig[1]

                    # The bar separates commands
                    if trig[-1] == "|":
                        trig = trig[:-1] + "<Bar>"

                    # Special ones
                    if trig[0] == "<":
                        add = False
                        # Only allow these
                        for valid in ["Tab", "NL", "CR", "C-Tab", "BS"]:
                            if trig == "<%s>" % valid:
                                add = True
                        if not add:
                            continue

                    # Actually unmap it
                    vim.command("sunmap %s %s" % (option,trig))

class SnippetManager(object):
    def __init__(self):
        self._vstate = VimState()
        self._supertab_keys = None

        self.reset()

    def reset(self, test_error=False):
        self._test_error = test_error
        self._snippets = {}
        self._csnippets = []
        self._reinit()

    def jump_forwards(self):
        if not self._jump():
            return self._handle_failure(self.forward_trigger)

    def jump_backwards(self):
        if not self._jump(True):
            return self._handle_failure(self.backward_trigger)

    def expand(self):
        if not self._try_expand():
            self._handle_failure(self.expand_trigger)

    def list_snippets(self):
        before, after = self._get_before_after()
        snippets = self._snips(before, True)

        if not snippets:
            return True

        snippet = self._ask_snippets(snippets)
        if not snippet:
            return True

        self._do_snippet(snippet, before, after)

        return True


    def expand_or_jump(self):
        """
        This function is used for people who wants to have the same trigger for
        expansion and forward jumping. It first tries to expand a snippet, if
        this fails, it tries to jump forward.
        """
        rv = self._try_expand()
        if not rv:
            rv = self._jump()
        if not rv:
            self._handle_failure(self.expand_trigger)

    def add_snippet(self, trigger, value, descr, options, ft = "all", globals = None):
        if ft not in self._snippets:
            self._snippets[ft] = _SnippetDictionary()
        l = self._snippets[ft].add_snippet(
            Snippet(trigger, value, descr, options, globals or {})
        )

    def clear_snippets(self, triggers = [], ft = "all"):
        if ft in self._snippets:
            self._snippets[ft].clear_snippets(triggers)

    def add_extending_info(self, ft, parents):
        if ft not in self._snippets:
            self._snippets[ft] = _SnippetDictionary()
        sd = self._snippets[ft]
        for p in parents:
            if p in sd.extends:
                continue

            sd.extends.append(p)


    def backspace_while_selected(self):
        """
        This is called when backspace was pressed while vim was in select
        mode. For us this might mean that a TabStop was selected and it's
        content should be deleted.
        """
        if self._cs and (self._span_selected is not None):
            # This only happens when a default value is delted using backspace.
            # This does not change the buffer at all, only moves the cursor.
            self._vstate.update()
            feedkeys(r"i")
            self._chars_entered('')
        else:
            feedkeys(r"\<BS>")

    def cursor_moved(self):
        self._vstate.update()

        if not self._vstate.buf_changed and not self._expect_move_wo_change:
            self._check_if_still_inside_snippet()

        if not self._ctab:
            return

        if self._vstate.buf_changed and self._ctab:
            # Detect a carriage return
            if self._vstate.moved.col <= 0 and self._vstate.moved.line == 1:
                # Multiple things might have happened: either the user entered
                # a newline character or pasted some text which means we have
                # to copy everything he entered on the last line and keep the
                # indent vim chose for this line.
                lline = vim.current.buffer[self._vstate.ppos.line]

                # Another thing that might have happened is that a word
                # wrapped, in this case the last line is shortened and we must
                # delete what Vim deleted there
                line_was_shortened = len(self._vstate.last_line) > len(lline)

                # Another thing that might have happened is that vim has
                # adjusted the indent of the last line and therefore the line
                # effectively got longer. This means a newline was entered and
                # we quite definitively do not want the indent that vim added
                line_was_lengthened = len(lline) > len(self._vstate.last_line)

                user_didnt_enter_newline = len(lline) != self._vstate.ppos.col
                cline = vim.current.buffer[self._vstate.pos.line]
                if line_was_lengthened:
                    this_entered = vim.current.line[:self._vstate.pos.col]
                    self._chars_entered('\n' + cline + this_entered, 1)
                if line_was_shortened and user_didnt_enter_newline:
                    self._backspace(len(self._vstate.last_line)-len(lline))
                    self._chars_entered('\n' + cline, 1)
                else:
                    pentered = lline[self._vstate.ppos.col:]
                    this_entered = vim.current.line[:self._vstate.pos.col]

                    self._chars_entered(pentered + '\n' + this_entered)
            elif self._vstate.moved.line == 0 and self._vstate.moved.col<0:
                # Some deleting was going on
                self._backspace(-self._vstate.moved.col)
            elif self._vstate.moved.line < 0:
                # Backspace over line end
                self._backspace(1)
            else:
                line = vim.current.line

                chars = line[self._vstate.pos.col - self._vstate.moved.col:
                             self._vstate.pos.col]
                self._chars_entered(chars)

        self._expect_move_wo_change = False

    def entered_insert_mode(self):
        self._vstate.update()
        if self._cs and self._vstate.has_moved:
            self._reinit()
            self._csnippets = []

    ###################################
    # Private/Protect Functions Below #
    ###################################
    def _error(self, msg):
        msg = _vim_quote("UltiSnips: " + msg)
        if self._test_error:
            msg = msg.replace('"', r'\"')
            msg = msg.replace('|', r'\|')
            vim.command("let saved_pos=getpos('.')")
            vim.command("$:put =%s" % msg)
            vim.command("call setpos('.', saved_pos)")
        elif False:
            vim.command("echohl WarningMsg")
            vim.command("echomsg %s" % msg)
            vim.command("echohl None")
        else:
            vim.command("echoerr %s" % msg)

    def _reinit(self):
        self._ctab = None
        self._span_selected = None
        self._expect_move_wo_change = False

    def _check_if_still_inside_snippet(self):
        # Cursor moved without input.
        self._ctab = None

        # Did we leave the snippet with this movement?
        if self._cs and not (self._vstate.pos in self._cs.abs_span):
            self._csnippets.pop()

            self._reinit()

            self._check_if_still_inside_snippet()

    def _jump(self, backwards = False):
        jumped = False
        if self._cs:
            self._expect_move_wo_change = True
            self._ctab = self._cs.select_next_tab(backwards)
            if self._ctab:
                self._vstate.select_span(self._ctab.abs_span)
                self._span_selected = self._ctab.abs_span
                jumped = True
                if self._ctab.no == 0:
                    self._ctab = None
                    self._csnippets.pop()
                self._vstate.update()
            else:
                # This really shouldn't happen, because a snippet should
                # have been popped when its final tabstop was used.
                # Cleanup by removing current snippet and recursing.
                self._csnippets.pop()
                jumped = self._jump(backwards)
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
            if vim.eval("exists('g:SuperTabMappingForward')") != "0":
                self._supertab_keys = (
                    vim.eval("g:SuperTabMappingForward"),
                    vim.eval("g:SuperTabMappingBackward"),
                )
            else:
                self._supertab_keys = [ '', '' ]

        for idx, sttrig in enumerate(self._supertab_keys):
            if trigger.lower() == sttrig.lower():
                if idx == 0:
                    feedkey= r"\<c-n>"
                elif idx == 1:
                    feedkey = r"\<c-p>"
                # Use remap mode so SuperTab mappings will be invoked.
                mode = "m"
                break

        if feedkey:
            feedkeys(feedkey, mode)

    def _ensure_snippets_loaded(self):
        filetypes = vim.eval("&filetype").split(".") + [ "all" ]
        for ft in filetypes[::-1]:
            if len(ft) and ft not in self._snippets:
                self._load_snippets_for(ft)

        return filetypes

    def _get_before_after(self):
        """ Returns the text before and after the cursor as a
        tuple.
        """
        lineno,col = vim.current.window.cursor

        line = vim.current.line

        # Get the word to the left of the current edit position
        before, after = line[:col], line[col:]

        return before, after

    def _snips(self, before, possible):
        """ Returns all the snippets for the given text
        before the cursor. If possible is True, then get all
        possible matches.
        """
        filetypes = self._ensure_snippets_loaded()

        found_snippets = []
        for ft in filetypes[::-1]:
            found_snippets += self._find_snippets(ft, before, possible)

        # Search if any of the snippets overwrites the previous
        snippets = []
        for s in found_snippets:
            if s.overwrites_previous:
                snippets = []
            snippets.append(s)

        return snippets

    def _ask_snippets(self, snippets):
        """ Given a list of snippets, ask the user which one they
        want to use, and return it.
        """
        display = repr(
            [ "%i: %s" % (i+1,s.description) for i,s in
             enumerate(snippets)
            ]
        )

        try:
            rv = vim.eval("inputlist(%s)" % display)
            if rv is None or rv == '0':
                return None
            rv = int(rv)
            if rv > len(snippets):
                rv = len(snippets)
            return snippets[rv-1]
        except vim.error, e:
            if str(e) == 'invalid expression':
                return None
            raise

    def _do_snippet(self, snippet, before, after):
        """ Expands the given snippet, and handles everything
        that needs to be done with it. 'before' and 'after' should
        come from _get_before_after.
        """
        lineno,col = vim.current.window.cursor
        # Adjust before, maybe the trigger is not the complete word
        text_before = before[:-len(snippet.matched)]

        self._expect_move_wo_change = True
        if self._cs:
            # Determine position
            pos = self._vstate.pos
            p_start = self._ctab.abs_start

            if pos.line == p_start.line:
                end = Position(0, pos.col - p_start.col)
            else:
                end = Position(pos.line - p_start.line, pos.col)
            start = Position(end.line, end.col - len(snippet.matched))

            si = snippet.launch(text_before, self._ctab, start, end)

            self._update_vim_buffer()

            if si.has_tabs:
                self._csnippets.append(si)
                self._jump()
        else:
            self._vb = VimBuffer(text_before, after)

            start = Position(lineno-1, len(text_before))
            self._csnippets.append(snippet.launch(text_before, None, start))

            self._vb.replace_lines(lineno-1, lineno-1,
                       self._cs._current_text)

            self._jump()

    def _try_expand(self):
        self._expect_move_wo_change = False

        before, after = self._get_before_after()
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


    # Input Handling
    def _chars_entered(self, chars, del_more_lines = 0):
        if (self._span_selected is not None):
            self._ctab.current_text = chars

            moved = 0
            # If this edit changed the buffer in any ways we might have to
            # delete more or less lines, according how the cursors has moved
            if self._vstate.buf_changed:
                moved = self._span_selected.start.line - \
                        self._span_selected.end.line
            self._span_selected = None

            self._update_vim_buffer(moved + del_more_lines)
        else:
            self._ctab.current_text += chars
            self._update_vim_buffer(del_more_lines)


    def _backspace(self, count):
        self._ctab.current_text = self._ctab.current_text[:-count]
        self._update_vim_buffer()

    def _update_vim_buffer(self, del_more_lines = 0):
        if not len(self._csnippets):
            return

        s = self._csnippets[0]
        sline = s.abs_start.line
        dlines = s.end.line - s.start.line

        s.update()

        # Replace
        if self._vstate.buf_changed:
            dlines += self._vstate.moved.line
        dlines += del_more_lines
        self._vb.replace_lines(sline, sline + dlines,
                       s._current_text)
        ct_end = self._ctab.abs_end
        vim.current.window.cursor = ct_end.line +1, ct_end.col

        self._vstate.update()

    def _cs(self):
        if not len(self._csnippets):
            return None
        return self._csnippets[-1]
    _cs = property(_cs)

    def _parse_snippets(self, ft, fn, file_data=None):
        _SnippetsFileParser(ft, fn, self, file_data).parse()

    # Loading
    def _load_snippets_for(self, ft):
        self._snippets[ft] = _SnippetDictionary()
        for p in vim.eval("&runtimepath").split(',')[::-1]:
            pattern = p + os.path.sep + "UltiSnips" + os.path.sep + \
                    "*%s.snippets" % ft

            for fn in glob.glob(pattern):
                self._parse_snippets(ft, fn)

        # Now load for the parents
        for p in self._snippets[ft].extends:
            if p not in self._snippets:
                self._load_snippets_for(p)

    def _find_snippets(self, ft, trigger, potentially = False):
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

        parent_results = reduce( lambda a,b: a+b,
            [ self._find_snippets(p, trigger, potentially)
                for p in snips.extends ], [])

        return parent_results + snips.get_matching_snippets(
            trigger, potentially)


UltiSnips_Manager = SnippetManager()

