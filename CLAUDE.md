# UltiSnips

Snippet engine for Vim and Neovim. Plugin code lives in `pythonx/UltiSnips/`, docs in `doc/UltiSnips.txt`.

See `CONTRIBUTING.md` for full contributor guidelines.

## Branching

- Work on branches named `sirver/<issue-description>`.
- Use the `/mr` slash command to create merge requests.

## Testing

Every new feature or bug fix needs a test. Tests are integration tests that run Vim/Neovim inside tmux.

1. Start a tmux session: `tmux new -s vim` (leave it idle).
2. In another terminal: `./test_all.py` (or `./test_all.py <TestNamePrefix>` to filter).
3. For Neovim: `./test_all.py --vim nvim`

The test runner auto-detects Vim vs Neovim from the executable.

When a `tmux new -s vim` session is already running, run integration tests directly:

```
./test_all.py <TestNamePrefix>        # run matching tests
./test_all.py Transformation          # example: all transformation tests
```

Prefer running inside Docker for isolation:

```
make image_repro && make repro   # shell 1: build + launch container, then `tmux new -s vim`
make shell_in_repro              # shell 2: enter container, then `./test_all.py`
```

### Test framework gotchas

- Pre-existing buffer content goes in `text_before` / `text_after` — do **not** prepend it to `keys`.
  Content in `keys` is typed in insert mode and triggers iA snippets, mappings, abbreviations.
- `wanted` is the content **between** `text_before` and `text_after`; `VimTestCase.runTest` wraps it. Don't
  repeat the prefill text in `wanted`.
- Default `--retries 4` retries with progressively slower typing. Use `--retries 1` for clean single-run
  logs, but iA snippets with long triggers need more retries to type slowly enough — drop to `--retries 1`
  only when speed isn't the variable you're studying or monkey-patch the sleep time higher in that case.

### Debugging buffer-tracking issues

When the textobject tree appears corrupted (jumps land in the wrong place, tabstops disappear),
instrument the suspect sites with `pythonx/UltiSnips/debug.py` instead of trying to read the whole tree
at once. It provides `debug(msg)`, `debug_section(label="")`, `debug_snippet_stack(active_snippets)`,
and `echo_to_hierarchy(text_object)`. Importing the module clears the log file (default
`/tmp/file.txt`, override with `ULTISNIPS_DEBUG_PATH`); each line carries a monotonic-time prefix so
diffs line up. Typical sites: `SnippetManager._jump`, `SnippetManager._cursor_moved`,
`SnippetInstance.select_next_tab`, and the `_active_snippets.append` line in `_do_snippet`. Run the
failing test, then a control test with the suspected variable removed (e.g. popup vs. no popup), and
`diff` the two log files. The first divergence is usually the smoking gun.

Remove the imports/calls before committing.

### Vim popup ↔ UltiSnips facts

- `CursorMovedI` and `TextChangedI` are **suppressed while the completion popup is visible**;
  `TextChangedP` fires instead. `_cursor_moved` is bound to `CursorMovedI`, so popup-time edits queue in
  the listener but aren't drained until the popup closes.
- `autoload/UltiSnips.vim` defines `s:compensate_for_pum()` — calls `_cursor_moved()` if `pumvisible()`. It
  must be called at the top of every `UltiSnips#…` entry point that triggers expansion or jumping;
  otherwise `_try_expand` / `_jump` runs against a stale tree.

## Linting and Formatting

```
make lint       # ruff check
make format     # ruff format
```

CI enforces both. Install the pre-commit hook with `./scripts/install-hooks`.
