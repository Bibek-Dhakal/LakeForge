"""Evaluation helpers: table fingerprints, idempotency verification, scale benchmark."""

from __future__ import annotations

import json
import statistics
import time
from typing import Any

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from .batches import add_months, month_range
from .catalog import TABLES
from .delta_io import is_delta, read_delta
from .metrics import read_metrics
from .pipeline import run_batch, run_range
from .session import get_spark
from .settings import Settings
from .stages import PROCESS_STAGES


def fingerprint(spark: SparkSession, settings: Settings) -> dict[str, dict[str, Any]]:
    """Order-insensitive (row count, hash-sum) per materialised table."""
    out: dict[str, dict[str, Any]] = {}
    for name, info in TABLES.items():
        path = settings.table_path(info.layer, info.name)
        if not is_delta(spark, path):
            continue
        df = read_delta(spark, path)
        row = df.agg(
            F.count(F.lit(1)).alias("n"),
            F.sum(F.xxhash64(*[F.col(c) for c in df.columns]).cast("decimal(38,0)")).alias("h"),
        ).first()
        out[name] = {"rows": row["n"], "hash": str(row["h"])}
    return out


def verify_idempotency(
    settings: Settings, batch: str, spark: SparkSession | None = None
) -> dict[str, Any]:
    """Run bronze->gold twice for a batch and compare table fingerprints."""
    spark = spark or get_spark(settings)
    run_batch(settings, batch, spark, PROCESS_STAGES)
    first = fingerprint(spark, settings)
    run_batch(settings, batch, spark, PROCESS_STAGES)
    second = fingerprint(spark, settings)
    diffs = {
        k: {"first": first.get(k), "second": second.get(k)}
        for k in first
        if first[k] != second.get(k)
    }
    return {
        "batch": batch,
        "identical": not diffs and first.keys() == second.keys(),
        "diffs": diffs,
        "tables": first,
    }


def _query_latency_ms(settings: Settings, runs: int = 5) -> float:
    import duckdb
    from deltalake import DeltaTable

    dataset = DeltaTable(settings.table_path("gold", "daily_summary")).to_pyarrow_dataset()
    con = duckdb.connect()
    con.register("daily_summary", dataset)
    sql = "SELECT is_weekend, count(*), sum(revenue), avg(tip_pct) FROM daily_summary GROUP BY 1"
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        con.execute(sql).fetchall()
        samples.append((time.perf_counter() - t0) * 1000)
    return round(statistics.median(samples), 2)


def run_benchmark(
    settings: Settings, month_counts: list[int], first_month: str = "2024-01"
) -> list[dict[str, Any]]:
    """Run the pipeline from scratch at several data scales (in isolated lake roots)."""
    results = []
    for n in month_counts:
        scale = settings.with_lake_root(
            settings.lake_root.parent / f"{settings.lake_root.name}_bench_{n}m"
        )
        months = month_range(first_month, add_months(first_month, n - 1))
        spark = get_spark(scale, app=f"lakeforge-bench-{n}m")
        t0 = time.perf_counter()
        run_range(scale, months[0], months[-1], spark=spark)
        elapsed = time.perf_counter() - t0
        trips = read_delta(spark, scale.table_path("silver", "trips")).count()
        stage_seconds: dict[str, float] = {}
        for rec in read_metrics(scale):
            stage_seconds[rec["stage"]] = round(
                stage_seconds.get(rec["stage"], 0) + rec["duration_s"], 2
            )
        results.append(
            {
                "months": n,
                "silver_trips": trips,
                "total_seconds": round(elapsed, 2),
                "rows_per_second": round(trips / elapsed, 1) if elapsed else None,
                "stage_seconds": stage_seconds,
                "gold_query_latency_ms": _query_latency_ms(scale),
            }
        )
    settings.meta_dir.mkdir(parents=True, exist_ok=True)
    (settings.meta_dir / "benchmark.json").write_text(json.dumps(results, indent=2))
    return results
