# UltiSnips Modernization Plan

**Audience:** Engineers working on UltiSnips internals
**Status:** Living document — check items off as they land

The codebase has already been significantly modernized (f-strings, Python
3.11+, ruff enforcement, pathlib, modern `super()`). This document tracks
remaining cleanup, correctness, and stability improvements.

---

## Done

- [x] `SnippetSyntaxError` skipped parent init — fixed to use `super().__init__`
- [x] Old-style explicit `__init__` calls — converted to `super()` throughout
- [x] `_Placeholder` namedtuple name mismatch — converted to typed `NamedTuple`
- [x] Dead `hasattr(vim, "bindeval")` branch — removed
- [x] Stray fold marker in `autoload/UltiSnips.vim` — removed
- [x] `namedtuple` → typed `NamedTuple` for `_Placeholder` and `_VisualContent`
- [x] `TextObject.__init__` dual-purpose constructor — split into explicit-args
      only; subclasses now extract token fields themselves
- [x] `_is_pos_zero` mixed-type comparison — added explanatory comment
- [x] Unit tests not run in CI — fixed imports, added pytest step
