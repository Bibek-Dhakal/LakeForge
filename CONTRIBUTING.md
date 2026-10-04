# Contributing to LakeForge

## Setup (Docker-First)

We use a strict **Docker-first development environment** to eliminate host-machine setup friction (like installing Java
17, configuring Hadoop DLLs on Windows, or resolving Python 3.13+ `cloudpickle` conflicts).

Everything runs inside the isolated `dev` container, which maps your local repository folder live:

```bash
cp .env.example .env

# Run fast unit tests (no Spark)
docker compose --profile dev run --rm dev pytest -m "not spark"

# Run the complete integration test suite
docker compose --profile dev run --rm dev pytest

# Run the code linter (Ruff)
docker compose --profile dev run --rm dev ruff check .
docker compose --profile dev run --rm dev ruff format --check .
```

*(Optional but highly recommended: Install `pre-commit` on your host machine to format files automatically before every
git commit via `pip install pre-commit && pre-commit install`)*.

## Conventional Commits (strictly enforced)

Every commit message **and every PR title** must follow `type(scope): description`.
These messages drive automated versioning and `CHANGELOG.md` generation through
`release-please` Release PRs.

| Prefix                                                                      | Effect                                |
|-----------------------------------------------------------------------------|---------------------------------------|
| `feat:`                                                                     | minor release, listed under Features  |
| `fix:`                                                                      | patch release, listed under Bug Fixes |
| `feat!:` / `fix!:` / `BREAKING CHANGE:` footer                              | major release                         |
| `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `chore:` | no release by themselves              |

Example: `fix(silver): keep latest batch when merging late duplicates`

## Pull requests

1. Branch from `main`, keep PRs focused.
2. Add or update tests for behaviour changes; idempotency and conservation tests must stay green.
3. Make sure tests and linting pass via Docker (`docker compose --profile dev run --rm dev pytest`).
4. Use a Conventional Commit PR title. Changes merged to `main` are aggregated into the open
   Release PR; merging that PR cuts the release and updates `CHANGELOG.md`.
