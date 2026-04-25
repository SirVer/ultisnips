from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


# https://github.com/SirVer/ultisnips/issues/1527
#
# Reporter scenario: vimtex compiles a `.tex` file in the background and pops
# the quickfix open via `:copen` whenever the in-progress snippet body produces
# a parse error (`\begin{ite}` is invalid until the env name is finished).
# `copen` momentarily steals focus, firing BufEnter for the quickfix buffer,
# which used to call `UltiSnips#LeavingBuffer()` and tear down the snippet —
# the buffer-local `<buffer>` mappings on the original buffer were left
# orphaned because the unmap commands run while focus is still in the qf, so
# the next jump silently no-ops.
#
# Fix: classify quickfix and location-list windows alongside preview/floating
# in the LeavingBuffer guard, AND defer the check via `timer_start(0, ...)`
# because Vim sets the qf window's `&buftype` *after* BufEnter fires.
class QuickfixOpenedDuringSnippet_DoesNotClearSnippet_Issue1527(_VimTest):
    snippets = ("env", "\\begin{$1}\n\t$2\n\\end{$1}", "", "i")
    # `<c-l>` (chr 12) has no insert-mode default; we map it below to populate
    # the quickfix list, open it (which steals focus), and switch back — the
    # same focus dance vimtex does on each background compile.
    keys = "env" + EX + "itemize" + "\x0c" + JF + "stuff"
    wanted = "\\begin{itemize}\n\tstuff\n\\end{itemize}"

    def _extra_vim_config(self, vim_config):
        vim_config.extend(
            [
                "function! UltiSnipsTest_OpenQuickfix() abort",
                "  call setqflist([{'text': 'simulated error'}])",
                "  copen",
                "  wincmd p",
                "endfunction",
                "inoremap <c-l> <cmd>call UltiSnipsTest_OpenQuickfix()<cr>",
            ]
        )


# Same scenario as above but with a location-list (`:lopen`) instead of
# `:copen`. Both share `&buftype == 'quickfix'`, so the single guard covers
# both — this test pins that contract.
class LocationListOpenedDuringSnippet_DoesNotClearSnippet_Issue1527(_VimTest):
    snippets = ("env", "\\begin{$1}\n\t$2\n\\end{$1}", "", "i")
    keys = "env" + EX + "itemize" + "\x0c" + JF + "stuff"
    wanted = "\\begin{itemize}\n\tstuff\n\\end{itemize}"

    def _extra_vim_config(self, vim_config):
        vim_config.extend(
            [
                "function! UltiSnipsTest_OpenLocList() abort",
                "  call setloclist(0, [{'text': 'simulated error'}])",
                "  lopen",
                "  wincmd p",
                "endfunction",
                "inoremap <c-l> <cmd>call UltiSnipsTest_OpenLocList()<cr>",
            ]
        )
