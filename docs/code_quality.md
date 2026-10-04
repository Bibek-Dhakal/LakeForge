# Code Quality

> Checks (Ruff, whitespace/YAML/JSON/TOML hygiene) run on **`git commit`** via pre-commit, and
> commit messages are validated on **`commit-msg`**. CI re-runs `ruff` and `pytest` on every push
> and PR. Every check can also be run manually (below).

## Environment Setup

```bash
pip install -e ".[dev]"
pre-commit install          # default_install_hook_types installs pre-commit + commit-msg hooks
```

## Manual Execution Commands

```bash
pre-commit run --all-files                      # all files
pre-commit run                                  # staged files only
pre-commit run --from-ref origin/main --to-ref HEAD   # changes against a target branch
pre-commit run ruff-check --files src/lakeforge/silver.py   # specific file
```

## Isolated Tool Commands

```bash
ruff check .            # linter only
ruff check . --fix      # linter with autofix
ruff format .           # formatter only
ruff format --check .   # formatter dry run (as in CI)
```

## Maintenance & Cache

```bash
pre-commit autoupdate   # bump hook revisions to latest releases
pre-commit clean        # clear pre-commit cache
ruff clean              # clear Ruff cache
```

## Emergency Bypassing

```bash
git commit --no-verify -m "fix: hotfix"   # skips local hooks
SKIP=ruff-format git commit -m "fix: x"   # skips a single hook
```

Use bypasses sparingly: CI and the PR-title check still enforce the same rules.
