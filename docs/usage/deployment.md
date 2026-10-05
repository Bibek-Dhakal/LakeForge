# Deployment

## Docker

LakeForge relies strictly on Docker to eliminate host-machine dependencies (Java, Hadoop DLLs, specific Python
versions).

```bash
cp .env.example .env
docker compose up --build api                                   # API on :8000
docker compose --profile tools run --rm pipeline seed-db
docker compose --profile tools run --rm pipeline run --start 2024-01 --end 2024-03

# Run the Streamlit dashboard on :8501
docker compose --profile dev run --rm -p 8501:8501 dev streamlit run src/lakeforge/serving/dashboard.py
```

## Airflow Orchestration

LakeForge ships with two parallel Airflow architectures, fully automated via Docker Compose profiles.

### Option A: Lightweight (Development & Portfolios)

Uses the `standalone` command and a local SQLite database to minimize memory footprint.

```bash
docker compose --profile orchestration up --build airflow
```

### Option B: Production-Grade (Concurrency & Scale)

Uses a dedicated **PostgreSQL** database and the `LocalExecutor` to run the Webserver and Scheduler independently,
completely eliminating database locks.

```bash
docker compose --profile orchestration-prod up --build
```

*(Default credentials for the UI at `localhost:8080` are `admin` / `admin`).*

---

### Triggering DAGs

DAG `lakeforge_monthly` runs one month per DAG run (`@monthly`, `catchup=True`, retries with
backoff). Backfill a range (Airflow 2.x):

```bash
# For Option A (Standalone):
docker compose --profile orchestration exec airflow airflow dags backfill -s 2024-01-01 -e 2024-03-31 lakeforge_monthly

# For Option B (Production):
docker compose --profile orchestration-prod exec airflow-scheduler airflow dags backfill -s 2024-01-01 -e 2024-03-31 lakeforge_monthly
```

Re-running a month is safe: every stage is idempotent.

## Observability

Start the observability stack in the background:

```bash
docker compose --profile observability up -d prometheus grafana
```

- **Prometheus UI:** Available at `http://localhost:9090`.
    - Navigate to **Status -> Targets** to confirm the `api:8000/metrics` endpoint is up and actively scraping.
    - Use the main query bar to inspect LakeForge metrics directly (e.g., `lakeforge_freshness_slo_breached` or
      `lakeforge_stage_failed`).
- **Grafana UI:** Available at `http://localhost:3000` (default login is `admin` / `admin`).
    - To connect Prometheus, go to **Connections -> Data sources -> Add data source -> Prometheus**. Set the URL to
      `http://prometheus:9090` and click "Save & test".
    - You can then use the **Explore** view to visualize LakeForge metrics or set up alert rules on
      `lakeforge_freshness_slo_breached == 1` or `lakeforge_stage_failed == 1`.
- **Live Logs:** To view raw streaming container logs from the terminal, run `docker compose logs -f`.

## Public URL

Deploy the `serving` image (or the Streamlit dashboard) to any container host; mount or bake a
gold snapshot. See [roadmap](../roadmap.md).
