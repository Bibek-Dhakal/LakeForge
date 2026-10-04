# Contributing to LakeForge

## Setup

```bash
pip install -e ".[dev,spark,serving]"
pre-commit install          # installs pre-commit and commit-msg hooks
pytest -m "not spark"       # fast tests
pytest                      # full suite (needs Java 17)
```

Code style is enforced by Ruff (see [docs/code_quality.md](docs/code_quality.md)).

## Conventional Commits (strictly enforced)

Every commit message **and every PR title** must follow `type(scope): description`.
These messages drive automated versioning and `CHANGELOG.md` generation through
`release-please` Release PRs.

| Prefix | Effect |
|---|---|
| `feat:` | minor release, listed under Features |
| `fix:` | patch release, listed under Bug Fixes |
| `feat!:` / `fix!:` / `BREAKING CHANGE:` footer | major release |
| `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `chore:` | no release by themselves |

Example: `fix(silver): keep latest batch when merging late duplicates`

## Pull requests

1. Branch from `main`, keep PRs focused.
2. Add or update tests for behaviour changes; idempotency and conservation tests must stay green.
3. Make sure `ruff check .`, `ruff format --check .` and `pytest` pass.
4. Use a Conventional Commit PR title. Changes merged to `main` are aggregated into the open
   Release PR; merging that PR cuts the release and updates `CHANGELOG.md`.
