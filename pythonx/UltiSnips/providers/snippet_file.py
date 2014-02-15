#!/usr/bin/env python
# encoding: utf-8

"""Code to provide access to UltiSnips files from disk."""

import glob
import os

from UltiSnips.providers._base import SnippetProvider
from UltiSnips.providers.ultisnips_file import parse_snippets_file
from UltiSnips.snippet_definition import SnippetDefinition
import UltiSnips._vim as _vim

def _plugin_dir():
    """Calculates the plugin directory for UltiSnips."""
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


def base_snippet_files_for(ft, default=True):
    """Returns a list of snippet files matching the given filetype (ft).
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

    paths = _vim.eval("&runtimepath").split(',')
    if _should_reverse_search_path():
        paths = paths[::-1]

    base_snippets = os.path.realpath(os.path.join(_plugin_dir(), "UltiSnips"))
    ret = []
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

class SnippetSyntaxError(RuntimeError):
    """Thrown when a syntax error is found in a file."""
    def __init__(self, filename, line_index, msg):
        RuntimeError.__init__(self, "%s in %s:%d" % (
            msg, filename, line_index))

class UltiSnipsFileProvider(SnippetProvider):
    """Manages all snippets definitions found in rtp."""

    def get_snippets(self, filetypes, before, possible):
        for ft in filetypes:
            self._ensure_loaded(ft)

        return SnippetProvider.get_snippets(self, filetypes, before, possible)

    def _ensure_loaded(self, ft, already_loaded=None):
        """Make sure that the snippets for 'ft' and everything it extends are
        loaded."""
        if not already_loaded:
            already_loaded = set()

        if ft in already_loaded:
            return
        already_loaded.add(ft)

        if self._needs_update(ft):
            self._load_snippets_for(ft)

        for parent in self._snippets[ft].extends:
            self._ensure_loaded(parent, already_loaded)

    def _needs_update(self, ft):
        """Returns true if any files for 'ft' have changed and must be
        reloaded."""
        if ft not in self._snippets:
            return True
        elif self._snippets[ft].has_any_file_changed():
            return True
        else:
            cur_snips = set(base_snippet_files_for(ft))
            old_snips = set(self._snippets[ft].files)
            if cur_snips - old_snips:
                return True
        return False

    def _load_snippets_for(self, ft):
        """Load all snippets for the given 'ft'."""
        if ft in self._snippets:
            del self._snippets[ft]
        for fn in base_snippet_files_for(ft):
            self._parse_snippets(ft, fn)
        # Now load for the parents
        for parent_ft in self._snippets[ft].extends:
            if parent_ft not in self._snippets:
                self._load_snippets_for(parent_ft)

    def _parse_snippets(self, ft, filename):
        """Parse the file 'filename' for the given 'ft' and watch it for
        changes in the future. 'file_data' can be injected in tests."""
        self._snippets[ft].addfile(filename)
        file_data = open(filename, "r").read()
        for event, data in parse_snippets_file(file_data):
            if event == "error":
                msg, line_index = data
                filename = _vim.eval("""fnamemodify(%s, ":~:.")""" %
                        _vim.escape(filename))
                raise SnippetSyntaxError(filename, line_index, msg)
            elif event == "clearsnippets":
                # TODO(sirver): clear snippets should clear for
                # more providers, not only ultisnips files.
                triggers, = data
                self._snippets[ft].clear_snippets(triggers)
            elif event == "extends":
                # TODO(sirver): extends information is more global
                # than one snippet provider.
                filetypes, = data
                self._add_extending_info(ft, filetypes)
            elif event == "snippet":
                trigger, value, description, options, globals = data
                self._snippets[ft].add_snippet(
                    SnippetDefinition(trigger, value, description, options,
                        globals), filename
                )
            else:
                assert False, "Unhandled %s: %r" % (event, data)

    def _add_extending_info(self, ft, parents):
        """Add the list of 'parents' as being extended by the 'ft'."""
        sd = self._snippets[ft]
        for parent in parents:
            if parent in sd.extends:
                continue
            sd.extends.append(parent)
