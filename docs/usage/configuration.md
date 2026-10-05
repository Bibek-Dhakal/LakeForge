# Configuration & CLI

Copy `.env.example` to `.env`. All values are read once in `lakeforge/settings.py`.

## Environment variables

| Name                          | Type       | Default                      | Description                                                                       |
|-------------------------------|------------|------------------------------|-----------------------------------------------------------------------------------|
| `LAKE_ROOT`                   | path       | `./data/lake`                | Root of landing/bronze/silver/gold/quarantine/meta                                |
| `SOURCE_DB_PATH`              | path       | `./data/source/reference.db` | SQLite reference source                                                           |
| `CONFIG_DIR`                  | path       | `./config`                   | Folder with `quality_rules.yaml`, `access_policy.yaml`                            |
| `TAXI_BASE_URL`               | url or dir | TLC CloudFront URL           | Where `yellow_tripdata_YYYY-MM.parquet` is fetched (a local folder works offline) |
| `ZONES_URL`                   | url        | TLC zone lookup CSV          | Used by `seed-db`                                                                 |
| `WEATHER_URL`                 | url        | Open-Meteo archive           | Weather API endpoint                                                              |
| `WEATHER_LAT` / `WEATHER_LON` | float      | `40.7128` / `-74.0060`       | Weather location                                                                  |
| `WEATHER_TIMEZONE`            | string     | `America/New_York`           | Weather day boundaries                                                            |
| `HTTP_TIMEOUT_S`              | int        | `60`                         | HTTP timeout                                                                      |
| `HTTP_RETRIES`                | int        | `4`                          | Attempts with exponential backoff                                                 |
| `LATE_ARRIVAL_DAYS`           | int        | `7`                          | Late-arrival window before the batch month start                                  |
| `FRESHNESS_SLO_HOURS`         | float      | `26`                         | Max age of last successful gold build                                             |
| `SPARK_MASTER`                | string     | `local[*]`                   | Spark master (standalone cluster URL also works)                                  |
| `SPARK_DRIVER_MEMORY`         | string     | `4g`                         | Driver memory                                                                     |
| `SPARK_SHUFFLE_PARTITIONS`    | int        | `8`                          | Shuffle partitions (keep small locally)                                           |
| `API_KEYS`                    | string     | empty                        | `key:role,key:role`                                                               |
| `MAX_QUERY_ROWS`              | int        | `10000`                      | Row cap for API responses                                                         |
| `LOG_LEVEL`                   | string     | `INFO`                       | Python logging level                                                              |

## CLI

**Note:** LakeForge operates entirely within Docker. Prefix these commands with
`docker compose --profile tools run --rm pipeline` to execute them correctly.

| Command                                                      | Purpose                                                                                                      |
|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| `lakeforge seed-db`                                          | Build the SQLite reference DB from the public zone lookup                                                    |
| `lakeforge stage <name> --month YYYY-MM`                     | One stage: `ingest_files\|ingest_api\|ingest_db\|bronze_files\|bronze_api\|bronze_db\|silver\|gold\|catalog` |
| `lakeforge run --start YYYY-MM --end YYYY-MM [--stages ...]` | Full pipeline over a month range (backfill)                                                                  |
| `lakeforge verify --month YYYY-MM`                           | Run bronze to gold twice; exit code 1 if table fingerprints differ                                           |
| `lakeforge benchmark --months 1 3 [--first-month 2024-01]`   | Scale benchmark into `<lake>/meta/benchmark.json`                                                            |
| `lakeforge catalog`                                          | Regenerate `<lake>/meta/catalog.md` and `lineage.mmd`                                                        |

## Quality rules

Edit `config/quality_rules.yaml`. Types: `not_null`, `range`, `in_set`, `regex`, `expression`,
`unique`, `referential`. Expressions may use `{batch_start}`, `{batch_end}`, `{late_start}`.
Re-run the batch after changing rules; quarantine and silver converge deterministically.
