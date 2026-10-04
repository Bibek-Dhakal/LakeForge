# Deployment

## Docker

```bash
cp .env.example .env
docker compose up --build api                                   # API on :8000
docker compose --profile tools run --rm pipeline seed-db
docker compose --profile tools run --rm pipeline run --start 2024-01 --end 2024-03
```

## Airflow

```bash
docker compose --profile orchestration up --build airflow       # UI on :8080
```

DAG `lakeforge_monthly` runs one month per DAG run (`@monthly`, `catchup=True`, retries with
backoff). Backfill a range (Airflow 2.x):

```bash
airflow dags backfill -s 2024-01-01 -e 2024-03-31 lakeforge_monthly
```

Re-running a month is safe: every stage is idempotent.

## Observability

```bash
docker compose --profile observability up prometheus grafana
```

Prometheus scrapes `api:8000/metrics`. Add a Prometheus datasource in Grafana (`http://prometheus:9090`)
and alert on `lakeforge_freshness_slo_breached == 1` or `lakeforge_stage_failed == 1`.

## Public URL

Deploy the `serving` image (or the Streamlit dashboard) to any container host; mount or bake a
gold snapshot. See [roadmap](../roadmap.md).
