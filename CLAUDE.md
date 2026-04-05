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

Prefer running inside Docker for isolation:
```
make image_repro && make repro   # shell 1: build + launch container, then `tmux new -s vim`
make shell_in_repro              # shell 2: enter container, then `./test_all.py`
```

CI uses Docker across Vim 9.0/9.1/git, Neovim, and Python 3.10-3.13 (`.github/workflows/main.yml`).

## Formatting

```
make format
```

Runs `black` on all Python files.
