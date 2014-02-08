#!/usr/bin/env python
# encoding: utf-8

"""Parsing of snippet files."""

import re
import UltiSnips._vim as _vim

# TODO(sirver): This could just as well be a function. Also the
# interface should change to a stream of events - so that it does
# not need knowledge of SnippetManager.
class SnippetsFileParser(object):
    """Does the actual parsing."""

    def __init__(self, ft, fn, snip_manager, file_data=None):
        """Parser 'fn' as filetype 'ft'."""
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
        """Reports 'msg' as an error."""
        fn = _vim.eval("""fnamemodify(%s, ":~:.")""" % _vim.escape(self._fn))
        self._sm.report_error("%s in %s(%d)" % (msg, fn, self._idx + 1))

    def _line(self):
        """The current line or the empty string."""
        return self._lines[self._idx] if self._idx < len(self._lines) else ""

    def _line_head_tail(self):
        """Returns (first word, rest) of the current line."""
        parts = re.split(r"\s+", self._line().rstrip(), maxsplit=1)
        parts.append('')
        return parts[:2]

    def _goto_next_line(self):
        """Advances to and returns the next line."""
        self._idx += 1
        return self._line()

    def _parse_first(self, line):
        """Parses the first line of the snippet definition. Returns the
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
        """Parses the snippet that begins at the current line."""
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
            self._sm.add_snippet(
                trig, cv, desc, opts, self._ft, self._globals, fn=self._fn)
        else:
            self._error("Invalid snippet type: '%s'" % snip)

    def parse(self):
        """Parses the given file."""
        while self._line():
            head, tail = self._line_head_tail()
            if head == "extends":
                if tail:
                    self._sm.add_extending_info(self._ft,
                        [p.strip() for p in tail.split(',')])
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
