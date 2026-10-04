# Analytics API

Start: `uvicorn lakeforge.serving.app:app --port 8000` (interactive docs at `/docs`).
Send `X-API-Key: <key>`; keys map to roles through `API_KEYS`, roles map to tables in
`config/access_policy.yaml`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | Liveness |
| GET | `/metrics` | none | Prometheus metrics: freshness, quality pass-rate, quarantined rows, durations |
| GET | `/tables` | key | Tables visible to the caller's role |
| GET | `/tables/{name}?limit=&offset=` | key | Browse a permitted table |
| POST | `/query` | key | Body `{"sql": "...", "limit": 1000}`, read-only SQL |

```bash
curl -H "X-API-Key: change-me-analyst" localhost:8000/tables
curl -H "X-API-Key: change-me-analyst" -H "Content-Type: application/json" \
  -d '{"sql":"SELECT pickup_date, trips, revenue FROM gold_daily_summary ORDER BY 1 LIMIT 5"}' \
  localhost:8000/query
```

SQL rules: a single `SELECT`/`WITH` statement; DDL/DML, `COPY`, file readers and similar keywords
are rejected; only the caller's tables are registered and DuckDB external access is disabled.
Table names are catalog names (for example `gold_daily_summary`, `quarantine_taxi_trips`).
