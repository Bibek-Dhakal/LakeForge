# LakeForge

Medallion lakehouse ETL/ELT with **idempotent incremental processing**, **schema enforcement**,
**data-quality quarantine**, **role-based serving** and **parameterised backfills**, built on
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

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate        # Java 17 required for Spark
pip install -e ".[dev,spark,serving,dashboard]"
cp .env.example .env
pre-commit install

lakeforge seed-db                                         # SQLite reference source
lakeforge run --start 2024-01 --end 2024-01               # ingest -> bronze -> silver -> gold
lakeforge verify --month 2024-01                          # re-run twice, compare fingerprints
uvicorn lakeforge.serving.app:app --reload                # role-scoped SQL API
streamlit run src/lakeforge/serving/dashboard.py          # dashboard on gold
```

Windows users: prefer WSL2 or Docker (`docker compose --profile tools run --rm pipeline run ...`).

## Documentation

- [Usage](docs/usage/README.md): CLI, configuration reference, API reference
- [Architecture](docs/architecture/README.md): layers, data model, catalog and lineage
- [Testing](docs/testing/README.md): strategy, invariants, CI
- [Results](docs/results/README.md): performance report and evaluation outputs
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
