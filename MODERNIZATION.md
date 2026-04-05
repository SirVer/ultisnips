# UltiSnips Cleanup & Modernization

## Done

- [x] **M1**: Fix `.iteritems()` crash
- [x] **M2**: Update Vim version check (kept at 800, added comment)
- [x] **M3**: Fix mypy python_version
- [x] **M4**: Replace bare `except:` clauses
- [x] **M5**: Remove `__setslice__`/`__getslice__`
- [x] **M7**: Update ChangeLog
- [x] **M8**: Bump `actions/checkout` v2 → v4
- [x] **M9**: Expand `.gitignore`
- [x] **M11**: Remove Python 2 legacy (encoding headers, idioms)
- [x] **M12**: Remove `(object)` base class
- [x] **M13**: Modernize `super()` calls
- [x] **M14**: Use `exist_ok=True`
- [x] **M15**: `%` formatting → f-strings
- [x] **M16**: `optparse` → `argparse`
- [x] **M17**: `subprocess.call` → `subprocess.run`
- [x] **M18**: Move mypy.ini into pyproject.toml
- [x] **M19**: Replace black+pylint with ruff (+ stricter rule sets)
- [x] **M21**: Add lint enforcement (CI job + pre-commit hook)
- [x] **M10**: Standardize on pathlib
- [x] Remove compatibility.py (inlined into vim_helper.py)
- [x] Convert remaining `.format()` calls to f-strings
- [x] Unify shebang lines
- [x] Remove pylint annotations
- [x] **Modernize Vim-Python data exchange** — replace `vim.command("let g:var = ...")` with `py3eval()`/`vim.vars[]` to eliminate string-escaping edge cases. Scope needs investigation.
- [x] **M22**: Migrate remaining `vim.command("let var = ...")` in `UltiSnips.vim` to `py3eval()`
- [x] **M23**: Remove dead `__setslice__`/`__getslice__` from `buffer_proxy.py`
- [x] **M24**: Fix typo "occured" → "occurred" in error message
- [x] **M25**: Replace string concatenation with f-string in user warning
- [x] **M26**: Complete `super()` migration in text_objects
- [x] **M27**: Replace `not len(x)` with `not x`
- [x] **M28**: Replace `glob.glob()` with `Path.glob()`
- [x] **M29**: Add missing shebang to `err_to_scratch_buffer.py`
- [x] **M30**: Fix docstring spelling in `buffer_proxy.py`
- [x] **M36**: Use `strict=True` in `zip()` calls in `diff.py` and `python_code.py`
- [x] **M37**: Remove `vim_helper.command()` wrapper, use `vim.command()` directly

## Remaining

### Structural

- [ ] **M34**: Refactor SnippetManager — ~990 lines, handles UI, sourcing, expansion, and buffer tracking. Natural seams: key mapping setup/teardown (`_setup_inner_state`/`_teardown_inner_state`), file-to-edit logic (already mostly free functions), change tracking (`_cursor_moved`/`_track_change`), SuperTab compat (`_handle_failure`). Significant scope, needs careful testing.
