"""Bronze layer: schema-enforced, append-only per batch, duplicates retained with batch lineage."""

from __future__ import annotations

import json

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from .contracts import PAYMENT_TYPES, TAXI_TRIPS, WEATHER_DAILY, ZONES, Contract
from .delta_io import read_delta, write_replace_where
from .ingest.api import DAILY_FIELDS, FILENAME, rows_from_payload
from .ingest.files import taxi_filename
from .ingest.landing import read_manifest
from .lineage import record_lineage
from .metrics import StageRecord, stage_run
from .schema_policy import enforce
from .settings import Settings


def conform(df: DataFrame, contract: Contract) -> tuple[DataFrame, dict]:
    """Lower-case columns, enforce the contract (may raise), cast to contract types."""
    df = df.toDF(*[c.lower() for c in df.columns])
    diff = enforce(contract, dict(df.dtypes))
    for col, dtype in contract.columns.items():
        if col in df.columns:
            df = df.withColumn(col, F.col(col).cast(dtype))
        else:
            df = df.withColumn(col, F.lit(None).cast(dtype))
    ordered = [*contract.columns, *diff.added]
    summary = {
        "schema_added": list(diff.added),
        "schema_missing_optional": diff.missing_optional,
        "schema_widened": {k: list(v) for k, v in diff.widened.items()},
    }
    return df.select(*ordered), summary


def _write_bronze(
    settings: Settings,
    table: str,
    df: DataFrame,
    contract: Contract,
    batch: str,
    source: str,
    source_file: str,
    ingested_at: str,
    rec: StageRecord,
) -> None:
    conformed, summary = conform(df, contract)
    rec.extra.update(summary)
    out = (
        conformed.withColumn("_batch_id", F.lit(batch))
        .withColumn("_source", F.lit(source))
        .withColumn("_ingested_at", F.lit(ingested_at).cast("timestamp"))
        .withColumn("_source_file", F.lit(source_file))
    )
    path = settings.table_path("bronze", table)
    write_replace_where(
        out, path, f"_batch_id = '{batch}'", partition_by=["_batch_id"], merge_schema=True
    )
    rec.rows_out = read_delta(df.sparkSession, path).filter(F.col("_batch_id") == batch).count()


def load_taxi(spark: SparkSession, settings: Settings, batch: str) -> None:
    landed = read_manifest(settings, "files", batch)
    name = taxi_filename(batch)
    with stage_run(settings, "bronze_files", batch, "taxi_trips") as rec:
        df = spark.read.parquet(landed.path(name).as_posix())
        rec.rows_in = df.count()
        _write_bronze(
            settings, "taxi_trips", df, TAXI_TRIPS, batch, "nyc_tlc_files", name,
            landed.ingested_at, rec,
        )  # fmt: skip
        record_lineage(settings, "bronze_files", batch, ["landing_files"], ["bronze_taxi_trips"])


def load_weather(spark: SparkSession, settings: Settings, batch: str) -> None:
    landed = read_manifest(settings, "api", batch)
    with stage_run(settings, "bronze_api", batch, "weather_daily") as rec:
        payload = json.loads(landed.path(FILENAME).read_text(encoding="utf-8"))
        rows = rows_from_payload(payload)
        schema = StructType(
            [
                StructField("date", StringType()),
                *[StructField(f, DoubleType()) for f in DAILY_FIELDS],
            ]
        )
        df = spark.createDataFrame(
            [(r["date"], *[r[f] for f in DAILY_FIELDS]) for r in rows], schema
        )
        rec.rows_in = len(rows)
        _write_bronze(
            settings, "weather_daily", df, WEATHER_DAILY, batch, "open_meteo_api", FILENAME,
            landed.ingested_at, rec,
        )  # fmt: skip
        record_lineage(settings, "bronze_api", batch, ["landing_api"], ["bronze_weather_daily"])


def load_reference(spark: SparkSession, settings: Settings, batch: str) -> None:
    landed = read_manifest(settings, "db", batch)
    for table, contract in (("zones", ZONES), ("payment_types", PAYMENT_TYPES)):
        with stage_run(settings, "bronze_db", batch, table) as rec:
            fname = f"{table}.parquet"
            df = spark.read.parquet(landed.path(fname).as_posix())
            rec.rows_in = df.count()
            _write_bronze(
                settings, table, df, contract, batch, "reference_sqlite", fname,
                landed.ingested_at, rec,
            )  # fmt: skip
            record_lineage(settings, "bronze_db", batch, ["landing_db"], [f"bronze_{table}"])
