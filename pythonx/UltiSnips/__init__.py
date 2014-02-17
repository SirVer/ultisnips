#!/usr/bin/env python
# encoding: utf-8

"""Entry point for all thinks UltiSnips."""

import vim  # pylint:disable=import-error

from UltiSnips.snippet_manager import SnippetManager

UltiSnips_Manager = SnippetManager(  # pylint:disable=invalid-name
    vim.eval('g:UltiSnipsExpandTrigger'),
    vim.eval('g:UltiSnipsJumpForwardTrigger'),
    vim.eval('g:UltiSnipsJumpBackwardTrigger'))
