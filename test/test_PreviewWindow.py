"""Regression tests for `:pedit` / preview-window interactions while a
snippet is active (GH #1168).

The original bug: a multi-step snippet was active, the user opened a
preview window with `:pedit` (or any plugin that did, e.g. `:DB` from
vim-dadbod), and then navigating *into* the preview hung Vim for large
previews. The preview window now classifies as an "aux" window that
LeavingBuffer ignores, so the snippet stays intact and navigating in
and out of the preview should be cheap.
"""

from test.constant import EX, JF
from test.vim_test_case import VimTestCase as _VimTest


class _PreviewBase(_VimTest):
    snippets = ("sel", "select ${2:*} from ${1:table} $0", "select", "i")
    preview_lines = 20

    def _extra_vim_config(self, vim_config):
        preview_file = self._temp_dir / "preview_content.txt"
        preview_file.write_text(
            "\n".join(f"row {i}" for i in range(self.preview_lines)) + "\n"
        )
        vim_config.append(f"let g:_preview_file = '{preview_file}'")
        vim_config.append("function! UltiSnipsTest_OpenPreview() abort")
        vim_config.append("  execute 'pedit ' . g:_preview_file")
        vim_config.append("endfunction")
        vim_config.append("inoremap <c-l> <cmd>call UltiSnipsTest_OpenPreview()<cr>")


class PreviewWindow_OpenedDuringSnippet_KeepsSnippet(_PreviewBase):
    # Expand snippet, fill first tabstop, open preview, jump back into
    # the snippet (jump should still work because the preview window is
    # classified as an aux window).
    keys = "sel" + EX + "users" + "\x0c" + JF + "id, name"
    wanted = "select id, name from users "


class PreviewWindow_OpenedThenFocused_DoesNotHang(_PreviewBase):
    # The original report: opening the preview is fine; *navigating* into
    # it with `<C-w>w` was the part that hung for large content. This
    # test exercises that path with a long file and verifies we can
    # still get back to the snippet buffer and complete the jump.
    preview_lines = 500
    keys = (
        "sel"
        + EX
        + "users"
        + "\x0c"
        # Leave insert mode, jump to the preview window, then back to the
        # snippet buffer. If this hangs, the test framework's per-test
        # timeout will surface the failure.
        + "\x1b\x17w\x17W"
        + "a"
        + JF
        + "id, name"
    )
    wanted = "select id, name from users "
