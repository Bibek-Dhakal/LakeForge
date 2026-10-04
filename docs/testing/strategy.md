# Testing strategy

| Tier | Location | Needs Spark | Covers |
|---|---|---|---|
| Unit | `tests/test_*.py` | no | schema policy, batch windows, immutable landing, payload parsing, metrics, RBAC, SQL guard, API |
| Integration | `tests/integration/` (`@pytest.mark.spark`) | yes | quality engine (seeded bad-record recall, conservation), end-to-end pipeline, idempotent re-runs, late/duplicate data, additive and breaking schema changes |

```bash
pytest -m "not spark"                 # fast
pytest                                # everything, with coverage
pytest tests/integration -k rerun     # the idempotency test
```

Integration tests are offline: synthetic parquet is served from a local folder through
`TAXI_BASE_URL`, weather is pre-landed (landing re-runs reuse the manifest), and the reference
SQLite DB is built in a temp directory.

## Invariants asserted

- Re-run equality: row counts and hash-sums of every table identical after repeated runs.
- `rows_in == rows_valid + rows_quarantined` (also enforced at runtime).
- Seeded bad-record recall = 1.0 with correct rule names.
- Late arrival inside window accepted and flagged; outside window quarantined.
- Additive column absorbed; breaking type change fails the stage and records a failed metric.

## CI

`.github/workflows/ci.yml`: Conventional-Commit PR title check, Ruff, full pytest (Java 17 +
PySpark), Docker builds for both image targets.
