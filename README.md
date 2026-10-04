# LakeForge

Medallion lakehouse ETL/ELT with **idempotent incremental processing**, **schema enforcement**, **data-quality
quarantine**, **role-based serving** and **parameterised backfills**, built on
open-source tools only (Spark, Delta Lake, Airflow, DuckDB, FastAPI) and runnable on a laptop.

```text
files (NYC TLC) ┐
API (Open-Meteo)├─> landing (immutable) -> bronze -> validate ─┬─> silver (MERGE) -> gold -> API / dashboard
SQLite reference┘                                              └─> quarantine (rule + reason + batch)
```

## Why

Naive pipelines double-count on re-runs, drop bad rows silently and break on schema drift.
LakeForge demonstrates the opposite, with tests: re-running any batch yields identical table
state, every input row ends up in silver **or** quarantine, breaking schema changes halt the
pipeline, and consumers only see data through role-scoped permissions.

## Quick start (Docker-First)

To avoid Python version conflicts, Java dependencies, and complex Windows Hadoop configurations, **LakeForge is entirely
Dockerized**.

```bash
cp .env.example .env

# 1. Seed reference data and run the ELT pipeline for a month
docker compose --profile tools run --rm pipeline seed-db
docker compose --profile tools run --rm pipeline run --start 2024-01 --end 2024-01

# 2. Verify pipeline idempotency (rerun twice and compare hashes)
docker compose --profile tools run --rm pipeline verify --month 2024-01

# 3. Start the Analytics API (role-scoped SQL over Gold tables)
docker compose up api
```

In a separate terminal, query the API using DuckDB:

```bash
curl -H "X-API-Key: change-me-analyst" -H "Content-Type: application/json" \
  -d '{"sql":"SELECT pickup_date, trips, revenue FROM gold_daily_summary ORDER BY 1 LIMIT 5"}' \
  http://localhost:8000/query
```

## Documentation

- [Usage](docs/usage/README.md): CLI, configuration reference, API reference
- [Architecture](docs/architecture/README.md): layers, data model, catalog and lineage
- [Testing](docs/testing/README.md): strategy, invariants, CI
- [Data](docs/data/README.md): datasets and licensing notes
- [Roadmap](docs/roadmap.md)
- [Case study](docs/case_study.md)
- [Code quality](docs/code_quality.md)
- [Contributing](CONTRIBUTING.md)

## System invariants

1. Re-running any batch yields identical table state.
2. Raw data is immutable; downstream layers are reproducible from it.
3. Invalid records are quarantined with reasons, never silently dropped or passed.
4. Breaking schema changes halt the pipeline rather than corrupt tables.
5. Consumers access data only through role-scoped permissions.

## License

MIT, see [LICENSE](LICENSE).
