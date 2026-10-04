# Data model

```mermaid
erDiagram
    dim_date ||--o{ fact_trips_daily : pickup_date
    dim_zone ||--o{ fact_trips_daily : pu_location_id
    dim_payment_type ||--o{ fact_trips_daily : payment_type_id
    dim_date ||--|| daily_summary : pickup_date
    fact_trips_daily {
        date pickup_date
        long pu_location_id
        long payment_type_id
        long trips
        long passengers
        decimal distance_miles
        decimal fare_amount
        decimal tip_amount
        decimal tolls_amount
        decimal total_amount
        long trip_seconds
    }
    daily_summary {
        date pickup_date
        long trips
        decimal revenue
        double avg_trip_minutes
        decimal tip_pct
        boolean is_weekend
        double temp_max_c
        double precip_mm
    }
```

| Table | Grain / key | Notes |
|---|---|---|
| `silver_trips` | `trip_id` = sha256(vendor, pickup, dropoff, PU, DO); partitioned by `pickup_date` | `trip_seconds`, `is_late_arrival`, `_batch_id`, `_ingested_at` |
| `silver_weather_daily` | `weather_date` | temp max/min (C), precipitation (mm) |
| `silver_zones` / `silver_payment_types` | business id | latest `updated_at` wins |
| `gold_fact_trips_daily` | pickup_date x pickup zone x payment type | additive measures |
| `gold_daily_summary` | pickup_date | KPIs + weather; ML feature table |
| `gold_dim_*` | surrogate = source id | dimensions rebuilt each run |
| `quarantine_*` | batch + row | `_failed_rules`, `_reasons`, `_record` (original row JSON) |

The full, generated, per-run column listing lives in `<LAKE_ROOT>/meta/catalog.md`.
