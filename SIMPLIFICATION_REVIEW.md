# Simplification review (post-4.0 bug-fix sprint)

## Summary

After 41 commits and ~150 bug/feature tickets landed since the 4.0 tag, this
pass reviews the resulting tree for dead code, duplication, accidental
complexity, inconsistent patterns, and over-defensive code. The codebase is in
better shape than the headline LOC delta suggests: most of the recent fixes
were minimum-scope and arrived with their own tests and explanatory comments,
so structural drift is limited.

| Metric                            | Value |
| ---                               | ---   |
| Files touched by this review      | 7     |
| Net LOC delta (excl. ChangeLog)   | -19 (+16, -35) |
| ChangeLog additions               | +143  |
| Behavior changes                  | 0     |
| Tests added                       | 0     |
| Tests removed                     | 0     |
| Public APIs touched               | 0     |

Three categories of change were applied; everything else was either verified
clean or explicitly deferred (with rationale, below).

1. **Doc fixes** - the table of contents had drifted past 4.10.3, and the
   `post_finish` section still showed a `post_jump` example carried over from
   when the section was copied.
2. **Compatibility shims for Vim < 9.1** - removed two `exists('*...')` checks
   that guarded against functions which have been present since Vim 8.0 /
   7.3.694. The minimum supported Vim is now 9.1 (4.0 baseline).
3. **Light deduplication** - one snippet-file glob pattern list was duplicated
   in two helpers in `pythonx/UltiSnips/snippet/source/file/ulti_snips.py`,
   collapsed by having one call the other.

Two bookkeeping fixes also landed: an incorrect statement in the new ChangeLog
entry I drafted (the `visual_text` exposure went only to `post_jump`, not all
three actions) and a dead-branch `is None` check in `SnippetDictionary` whose
sentinel is `float("-inf")`.

The deferred findings are listed at the end. None of them are bugs in their
own right; they are mostly cosmetic, deeply context-dependent, or genuine
design debt that does not belong in a polish pass.

---

## Changes applied

### `ChangeLog`

- **What**: Added the post-4.0 `next:` section with the 41 commits since the
  4.0 tag, grouped per the existing style (New features / Breaking changes /
  Bug fixes / Infrastructure) and cross-referenced to issue/PR numbers.
- **Why**: The sprint was complete and the file still pointed at
  `version 4.0 (10-May-2026):` as the most recent entry.
- **Risk**: None. Pure addition; no version number or date assigned per the
  task brief.

A factual correction was also folded in for the `visual_text` exposure: my
first draft of the entry claimed the locals were now available in
`post_expand`, `post_jump`, and `post_finish`. The commit (#1673) only added
them to `post_jump`. The instance-level snapshot improvement that the same
commit shipped *does* benefit any later reader of `snippet_instance.visual_content`,
so that part stays. Entry now reads accordingly.

### `doc/UltiSnips.txt` - table of contents

- **What**: Added `4.10.4 Post-finish actions ... |UltiSnips-post-finish-actions|`
  to the TOC at line 57.
- **Why**: The `post_finish` action and its tag (`*UltiSnips-post-finish-actions*`,
  line 1947 of the help file) were added in #1672 but the TOC at the top of
  the file was not updated. Help-file readers browsing the structure could
  miss the feature.
- **Risk**: None. TOC entry is descriptive, the actual section already
  exists.

### `doc/UltiSnips.txt` - `post_finish` example block

- **What**: The example under `*UltiSnips-post-finish-actions*` previously
  used `post_jump "..."` and an `insert_method_call` helper carried over
  verbatim from the `post_jump` section. The "Note: It is also possible to
  trigger snippet expansion from the jump action" sentence was likewise
  copied from `post_jump`. Replaced both with a concise example that
  matches the section's stated purpose - pairing `pre_expand` with
  `post_finish` for setup/teardown that survives any exit path.
- **Why**: The previous example didn't demonstrate `post_finish` at all and
  was likely to confuse readers. The replacement is shorter and matches the
  feature's documented motivation in #1415.
- **Risk**: Doc-only. No code or test reference the snippet body.

### `pythonx/UltiSnips/indent_util.py`

- **What**: `vim_helper.eval("exists('*shiftwidth') ? shiftwidth() : &shiftwidth")`
  -> `vim_helper.eval("shiftwidth()")`.
- **Why**: `shiftwidth()` has been built into Vim since 7.3.694. The 4.0
  release pinned the minimum supported Vim at 9.1, so the fallback to
  `&shiftwidth` is dead. (The fallback is also subtly wrong; `&shiftwidth`
  returns 0 to mean "use `&tabstop`", which `shiftwidth()` resolves
  internally.)
- **Risk**: Low. The version pin is enforced at plugin load
  (`plugin/UltiSnips.vim:9`) and the helper is only called from inside an
  active snippet, where `shiftwidth()` is guaranteed present.

### `autoload/UltiSnips.vim`

Three small changes:

1. **`exists('*timer_start')` removed** (`UltiSnips#LeavingBuffer`).
   `timer_start` is present since Vim 8.0; the synchronous fallback path
   is unreachable on supported Vim. The deferred call to
   `s:leaving_buffer_impl()` is the load-bearing one (deferral is what
   makes the quickfix/loclist `&buftype` race resolve correctly, per
   #1657).
2. **`endf` -> `endfunction`** in `UltiSnips#CursorMoved` and
   `UltiSnips#LeavingBuffer`. The other 30+ functions in the file use
   `endfunction`; the abbreviated form was an outlier. Cosmetic only.
3. (No further changes; the `s:compensate_for_pum` pattern and the
   `IsAuxWindow` classifier are intentional and were left alone.)

- **Risk**: None. `timer_start` and `endf` are universally available; the
  format change has no runtime effect.

### `pythonx/UltiSnips/snippet/source/file/ulti_snips.py`

- **What**: `UltiSnipsFileSource.get_all_snippet_files_for` was iterating
  the same `["%s.snippets", "%s_*.snippets", str(Path("%s") / "*")]`
  pattern list that `find_snippet_files` (line 21) already iterates.
  Both functions also call `normalize_file_path`. Collapsed
  `get_all_snippet_files_for` to delegate to `find_snippet_files` per
  directory.
- **Why**: The duplication grew during the #1637 dedupe fix, which added
  the canonicalization call in both places. Keeping only one source of
  truth reduces the chance of the two helpers drifting apart on the next
  pattern change.
- **Risk**: Low. The patterns are bit-identical, `find_snippet_files`
  already returns a `set[str]` of normalized paths, and the
  per-directory loop preserves the existing `is_dir()` guard.

### `pythonx/UltiSnips/snippet/source/file/base.py`

- **What**: Removed the empty `__init__(self): super().__init__()` from
  `SnippetFileSource`.
- **Why**: It does nothing Python wouldn't already do by default.
- **Risk**: None.

### `pythonx/UltiSnips/snippet/source/snippet_dictionary.py`

- **What**: `if self._clear_priority is None or priority > self._clear_priority:`
  -> `if priority > self._clear_priority:`.
- **Why**: The constructor initialises `self._clear_priority = float("-inf")`.
  `None` is unreachable, and the comparator is well-defined against the
  sentinel; `priority > float("-inf")` is true for any real number, so
  the first `clear_snippets()` call still wins exactly as before.
- **Risk**: None.

---

## Findings investigated but not changed

These were flagged during the survey and ruled out as either false positives,
already-clean code, or out of scope for a behavior-preserving polish pass.
They are recorded here so the next reviewer doesn't redo the analysis.

### `pythonx/UltiSnips/snippet_manager.py`

- **`_leaving_insert_mode` looks unused** (line 750). It *is* used - the
  `InsertLeave` autocmd at line 505 calls `UltiSnips#LeavingInsertMode()`
  in `autoload/UltiSnips.vim`, which forwards into this method. The Python
  side has no direct caller because the call comes through Vim's autocmd
  layer. Severity: **none (false positive)**.
- **Two-pass priority filter in `_snips()`** (lines 829-843). The two
  filters have different semantics: the inner one keeps the highest priority
  *per trigger*, the outer one (only on `partial=False`) keeps the highest
  priority *across all triggers* so a single snippet wins the expansion.
  Collapsing them would change the "Multiple matches" UX. Severity: **low,
  intentional**.
- **`assert self._change_provider is not None` at line 165**. Trivially true
  given the if/else above, but harmless. Severity: **trivial; leave**.
- **Local `snip_expanded_in_action` shadows `self._snip_expanded_in_action`**
  (line 710 vs 732). The local *snapshots* the instance variable after the
  post-jump action so a nested expansion's later mutation of the instance
  variable can't disturb the move-command decision at line 734. This is
  load-bearing in the #1638 fix; removing it would reintroduce the bug.
  Severity: **leave (intentional)**.
- **`_added_buffer_filetypes.insert(idx + 1, ft)` with `idx` from the
  except branch** (line 398). Fragile-looking but correct: `idx` is
  initialised to `-1` so the first miss inserts at position 0, and
  successive misses fall in after the previously-tracked filetype. A
  refactor to be explicit about the "not found" case is possible but
  doesn't shorten the code. Severity: **low; leave**.

### `pythonx/UltiSnips/text_objects/base.py`

- **`try: if ctab.number != child.number: continue except AttributeError: pass`**
  (lines 218-222) at the fall-through end of `_do_edit` for editable
  children. The AttributeError catches *two* cases: `ctab is None` (the
  default argument) and `child` not being a `TabStop` (it could be any
  `EditableTextObject`, e.g. a nested `SnippetInstance`). A direct
  `if ctab is not None and ctab.number != child.number:` rewrite would
  raise `AttributeError` on the second case and change behavior. Severity:
  **leave (load-bearing exception suppression)**.

### `pythonx/UltiSnips/text_objects/choices.py`

- **`overwrite_text` is referenced without being initialised on every
  branch** (line 129). All reachable paths set it in one of the two
  branches at lines 121/126 because `remained_choice_list` always has
  length 0 or 1 by the time we reach line 119 (the only branch that
  yields >1 elements sets `should_continue_input = True` and returns at
  line 115). Initialising `overwrite_text = None` at the top of the
  function would make the local control flow obvious without changing
  behavior - flagged as a possible follow-up cleanup. Severity:
  **low; defer**.

### `pythonx/UltiSnips/text_objects/snippet_instance.py`

- **`vc = _VimCursor(...)` is created inside `if cursorInsideLowest is not None:`
  and read in a symmetrical guard** (lines 133-151). Both reads of `vc` are
  guarded by the same condition, so there is no NameError reachable.
  Cosmetic rearrangement only. Severity: **leave**.

### `pythonx/UltiSnips/text_objects/python_code.py`

- **`TODO(sirver): The buffer should be passed into the object on construction`**
  (line 39). Long-standing design debt; out of scope for this pass.
- **`while snippet: try: ... except AttributeError: snippet = snippet._parent`**
  (PythonCode.__init__, lines 254-263). The walk-with-AttributeError works
  but is a popular code smell. Visual.__init__ uses the same shape; a
  shared helper (`find_enclosing_snippet_instance(text_object)`) would
  centralise it. Not done here to avoid touching hot paths. Severity:
  **low; defer**.

### `pythonx/UltiSnips/change_provider.py`

- **`_common_prefix_suffix` wrapper around `_suffix_match`** (lines 276-295).
  Looks like a one-line wrapper but it also computes the prefix before
  calling `_suffix_match`. The two call sites of `_common_prefix_suffix`
  do actually want both halves. Severity: **leave**.
- **`len(change) != 5` branch in `VimBufferProxy._apply_change`** (line 192).
  Reachable: `_get_diff` yields 5-tuples (multi-line, line-mode direction),
  `_get_line_diff` (single-line) yields 4-tuples and falls into the
  `len != 5` branch with column-mode direction. Severity: **leave**.

### `pythonx/UltiSnips/snippet/parsing/lexer.py`

- **`if self._text[self._idx] in ("\n", "\r\n"):`** (line 34). The
  `"\r\n"` element of the tuple can never match a single character so the
  check effectively only fires on `"\n"`. The behaviour on `\r\n` line
  endings is still correct (the `\r` advances `col`, then `\n` resets
  `line` and `col`), so removing the dead `"\r\n"` would not change
  output. Severity: **trivial; defer**.

### `pythonx/UltiSnips/vim_helper.py`

- **`if hasattr(vim, "bindeval"):`** (line 339). Real - Neovim's Python
  binding lacks `bindeval()`. Keep.
- **`_unmap_select_mode_mapping` is 70 lines of detailed parsing of
  `:smap` output**. Replaceable in principle by something Vim-native, but
  none of the alternatives I considered (`maparg` per-key, `:mapclear`
  scoped) preserve the "leave UltiSnips' own and a small allowlist of
  printables alone" behaviour that the user-facing
  `g:UltiSnipsRemoveSelectModeMappings` is documented to provide. Severity:
  **leave**.

### `pythonx/UltiSnips/vim_state.py`

- **`vim.command("let g:_ultisnips_reg_cache = {}")` repeated in `__init__`
  and `reset_register_cache`** (lines 65 and 116). Both set the cache to an
  empty dict, but `reset_register_cache` *also* resets `self._text_to_expect`.
  Extracting a helper for the one shared line would be net longer. Severity:
  **leave**.

### `autoload/unite/sources/ultisnips.vim`

- **`canditates` misspelling** throughout the file. Consistent within the
  file so it works, and Unite itself has been unmaintained since 2021.
  Cosmetic. Severity: **leave**.

### `after/plugin/UltiSnips_after.vim`

- **Second `UltiSnips#map_keys#MapKeys()` call**. Intentional - Vim
  sources `after/plugin/` *after* third-party plugins, so this is how
  UltiSnips wins the priority race against SuperTab and friends. The
  one-line comment explains this. Severity: **leave (well-known pattern)**.

### `watcher.lua`

- **Gitignored personal tool config** at the repo root (a `ctags`
  watcher for an external file-watcher tool). Not part of the plugin.
  Severity: **leave (not tracked)**.

### Other surveyed files with no findings

- `pythonx/UltiSnips/{position,error,debug,vim_encoding,text}.py`
- `pythonx/UltiSnips/snippet/parsing/{base,ulti_snips,snipmate}.py`
- `pythonx/UltiSnips/snippet/source/{base,added,file/common,file/snipmate}.py`
- `pythonx/UltiSnips/text_objects/{tabstop,mirror,viml_code,escaped_char,
  shell_code,transformation}.py`
- `pythonx/UltiSnips/err_to_scratch_buffer.py` (just rewritten in #1676)
- `pythonx/UltiSnips/buffer_proxy.py` (just rewritten in #1641)
- `pythonx/UltiSnips/snippet/definition/base.py`
- `autoload/UltiSnips/{listener,map_keys}.vim`
- `lua/ultisnips/on_bytes.lua`
- `rplugin/python3/deoplete/sources/ultisnips.py`
- `plugin/UltiSnips.vim` (rewritten in #1658)
- `scripts/slim-release.py`, `scripts/install-hooks`
- `Makefile`, `pyproject.toml`, `Dockerfile*`

---

## Findings beyond scope

None. The review surfaced one near-bug (`overwrite_text` reachability in
`choices.py`) but it is currently unreachable through the existing control
flow and so does not constitute a defect on master. It's flagged above as a
defer-candidate.

---

## Patterns worth knowing for the next round

A few cross-cutting observations from reading through the tree:

- **Tight coupling between `pythonx/UltiSnips/snippet_manager.py` and the
  text-object update loop**: `_jump`, `_do_snippet`, and
  `_current_snippet_is_done` each rebuild the same `use_proxy_buffer(...)`
  + `_action_context()` `with` block. A helper like
  `_run_in_action_context(snippet_instance, fn)` would shave ~20 lines and
  centralise the action-context entry/exit. Deferred because each call
  site passes a slightly different `snippets_stack` slice and changing
  one wrong invariant would corrupt the stack.
- **Three call sites walking a parent chain to find the enclosing
  `SnippetInstance`** (`PythonCode.__init__`,
  `text_objects/visual.py:_snippet_has_m_option`, and the snapshot read in
  the new `SnippetInstance.__init__`). Worth a shared utility if one of
  them needs to grow.
- **`pythonx/UltiSnips/snippet_manager.py:117` carries
  `TODO(sirver): This class is still too long`**. The 1153-line file is
  one of the two top-of-list refactor candidates; the other is
  `pythonx/UltiSnips/change_provider.py` at 689 lines. Both are
  out of scope here.

These notes are forward-looking - none of them imply the code is wrong
today.
