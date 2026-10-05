# Roadmap

Back to [README](../README.md).

## Done

- Three sources into landing, bronze, silver and gold, with quarantine, idempotent merges, backfills.
- RBAC API, dashboard, Prometheus metrics, Airflow DAG, CI, Docker.
- Shifted all development, testing, and execution entirely to Docker.
- Implemented dual Airflow deployment profiles supporting both lightweight SQLite and production-grade PostgreSQL
  architectures.

## Next

- [ ] Hosted gold snapshot plus deployed API/dashboard URL.
- [ ] Optional dbt-core models over gold; Great Expectations/Soda report alongside native rules.
- [ ] Open-source Unity Catalog or DataHub for catalog and access control.
- [ ] Grafana dashboard JSON and alert rules.

## Technical debt / known challenges

- Dimensions are type 1; add SCD2 for zones if history matters.
- Open-Meteo archive lags a few days; schedule month runs after month-end plus lag.
- Airflow 3 backfill CLI differs from Airflow 2; pin and document the version in use.
- Metrics are JSON files; move to a Delta table or Prometheus pushgateway for multi-writer setups.
- Row-level/column-level masking is not implemented (table-level RBAC only).
