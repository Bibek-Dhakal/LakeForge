"""Silver layer: validated, deduplicated, conformed tables written via idempotent MERGE."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from .batches import batch_context
from .delta_io import merge_into, read_delta, write_replace_where
from .lineage import record_lineage
from .metrics import StageRecord, stage_run
from .quality import load_rules, validate
from .settings import Settings

_TRIP_NATURAL_KEY = [
    "vendorid",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "pulocationid",
    "dolocationid",
]


def _latest(df: DataFrame, keys: list[str], order: list) -> DataFrame:
    window = Window.partitionBy(*keys).orderBy(*order)
    return df.withColumn("__rn", F.row_number().over(window)).filter("__rn = 1").drop("__rn")


def _validated(
    spark: SparkSession,
    settings: Settings,
    table: str,
    batch: str,
    rec: StageRecord,
    refs: dict[str, DataFrame] | None = None,
) -> DataFrame:
    df = read_delta(spark, settings.table_path("bronze", table)).filter(F.col("_batch_id") == batch)
    rules = load_rules(settings.rules_file, table)
    valid, bad = validate(df, rules, batch_context(batch, settings.late_arrival_days), refs)
    write_replace_where(
        bad,
        settings.table_path("quarantine", table),
        f"_batch_id = '{batch}'",
        partition_by=["_batch_id"],
    )
    rows_in, rows_bad, rows_valid = df.count(), bad.count(), valid.count()
    if rows_in != rows_valid + rows_bad:
        raise RuntimeError(
            f"conservation violated for {table}: in={rows_in} valid={rows_valid} bad={rows_bad}"
        )
    rec.rows_in, rec.rows_valid, rec.rows_quarantined = rows_in, rows_valid, rows_bad
    return valid


def silver_zones(spark: SparkSession, settings: Settings, batch: str) -> None:
    with stage_run(settings, "silver", batch, "zones") as rec:
        valid = _validated(spark, settings, "zones", batch, rec)
        src = _latest(
            valid.select(
                F.col("location_id").cast("long").alias("location_id"),
                "borough",
                "zone",
                "service_zone",
                "updated_at",
                "_batch_id",
                "_ingested_at",
            ),
            ["location_id"],
            [F.col("updated_at").desc(), F.col("_batch_id").desc()],
        )
        merge_into(
            spark, src, settings.table_path("silver", "zones"), ["location_id"],
            update_condition="s.updated_at >= t.updated_at",
        )  # fmt: skip
        rec.rows_out = src.count()
        record_lineage(
            settings, "silver", batch, ["bronze_zones"], ["quarantine_zones", "silver_zones"]
        )


def silver_payment_types(spark: SparkSession, settings: Settings, batch: str) -> None:
    with stage_run(settings, "silver", batch, "payment_types") as rec:
        valid = _validated(spark, settings, "payment_types", batch, rec)
        src = _latest(
            valid.select(
                F.col("payment_type_id").cast("long").alias("payment_type_id"),
                "payment_name",
                "updated_at",
                "_batch_id",
                "_ingested_at",
            ),
            ["payment_type_id"],
            [F.col("updated_at").desc(), F.col("_batch_id").desc()],
        )
        merge_into(
            spark, src, settings.table_path("silver", "payment_types"), ["payment_type_id"],
            update_condition="s.updated_at >= t.updated_at",
        )  # fmt: skip
        rec.rows_out = src.count()
        record_lineage(
            settings, "silver", batch, ["bronze_payment_types"],
            ["quarantine_payment_types", "silver_payment_types"],
        )  # fmt: skip


def silver_weather(spark: SparkSession, settings: Settings, batch: str) -> None:
    with stage_run(settings, "silver", batch, "weather_daily") as rec:
        valid = _validated(spark, settings, "weather_daily", batch, rec)
        src = _latest(
            valid.select(
                F.to_date("date").alias("weather_date"),
                F.col("temperature_2m_max").alias("temp_max_c"),
                F.col("temperature_2m_min").alias("temp_min_c"),
                F.col("precipitation_sum").alias("precip_mm"),
                "_batch_id",
                "_ingested_at",
            ),
            ["weather_date"],
            [F.col("_batch_id").desc()],
        )
        merge_into(
            spark, src, settings.table_path("silver", "weather_daily"), ["weather_date"],
            update_condition="s._batch_id >= t._batch_id",
        )  # fmt: skip
        rec.rows_out = src.count()
        record_lineage(
            settings, "silver", batch, ["bronze_weather_daily"],
            ["quarantine_weather_daily", "silver_weather_daily"],
        )  # fmt: skip


def silver_trips(spark: SparkSession, settings: Settings, batch: str) -> None:
    ctx = batch_context(batch, settings.late_arrival_days)
    with stage_run(settings, "silver", batch, "trips") as rec:
        refs = {
            "zones": read_delta(spark, settings.table_path("silver", "zones")),
            "payment_types": read_delta(spark, settings.table_path("silver", "payment_types")),
        }
        valid = _validated(spark, settings, "taxi_trips", batch, rec, refs)
        trip_id = F.sha2(
            F.concat_ws(
                "|", *[F.coalesce(F.col(c).cast("string"), F.lit("~")) for c in _TRIP_NATURAL_KEY]
            ),
            256,
        )
        trips = valid.select(
            trip_id.alias("trip_id"),
            F.col("vendorid").alias("vendor_id"),
            F.col("tpep_pickup_datetime").alias("pickup_ts"),
            F.col("tpep_dropoff_datetime").alias("dropoff_ts"),
            F.to_date("tpep_pickup_datetime").alias("pickup_date"),
            F.col("passenger_count").cast("int").alias("passenger_count"),
            "trip_distance",
            F.col("pulocationid").alias("pu_location_id"),
            F.col("dolocationid").alias("do_location_id"),
            F.col("payment_type").alias("payment_type_id"),
            "fare_amount",
            "tip_amount",
            "tolls_amount",
            "total_amount",
            (
                F.unix_timestamp("tpep_dropoff_datetime") - F.unix_timestamp("tpep_pickup_datetime")
            ).alias("trip_seconds"),
            (F.col("tpep_pickup_datetime") < F.lit(ctx["batch_start"]).cast("timestamp")).alias(
                "is_late_arrival"
            ),
            "_batch_id",
            "_ingested_at",
        )
        trips = _latest(
            trips,
            ["trip_id"],
            [
                F.col("_batch_id").desc(),
                F.col("total_amount").desc_nulls_last(),
                F.col("fare_amount").desc_nulls_last(),
                F.col("tip_amount").desc_nulls_last(),
                F.col("tolls_amount").desc_nulls_last(),
                F.col("passenger_count").desc_nulls_last(),
                F.col("trip_distance").desc_nulls_last(),
                F.col("payment_type_id").desc_nulls_last(),
            ],
        )
        merge_into(
            spark, trips, settings.table_path("silver", "trips"), ["trip_id", "pickup_date"],
            update_condition="s._batch_id >= t._batch_id",
            partition_by=["pickup_date"],
        )  # fmt: skip
        rec.rows_out = trips.count()
        record_lineage(
            settings, "silver", batch,
            ["bronze_taxi_trips", "silver_zones", "silver_payment_types"],
            ["quarantine_taxi_trips", "silver_trips"],
        )  # fmt: skip


def run_silver(spark: SparkSession, settings: Settings, batch: str) -> None:
    """Reference/dimension sources first so referential rules can resolve."""
    try:
        silver_zones(spark, settings, batch)
        silver_payment_types(spark, settings, batch)
        silver_weather(spark, settings, batch)
        silver_trips(spark, settings, batch)
    finally:
        spark.catalog.clearCache()
