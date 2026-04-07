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

CI uses Docker across Vim 9.1/9.2/git, Neovim 0.12, and Python 3.11-3.14 (`.github/workflows/main.yml`).

## Linting and Formatting

```
make lint       # ruff check
make format     # ruff format
```

CI enforces both. Install the pre-commit hook with `./scripts/install-hooks`.
