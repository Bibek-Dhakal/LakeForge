"""Gold layer: star schema + daily feature table. Exact decimal/long aggregation => deterministic."""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from .batches import batch_context
from .delta_io import is_delta, overwrite_table, read_delta, write_replace_where
from .lineage import record_lineage
from .metrics import stage_run
from .settings import Settings


def _dec(col: str) -> F.Column:
    return F.col(col).cast("decimal(18,2)")


def _build_dims(spark: SparkSession, settings: Settings, trips: DataFrame) -> None:
    zones = read_delta(spark, settings.table_path("silver", "zones"))
    overwrite_table(
        zones.select(F.col("location_id").alias("zone_key"), "borough", "zone", "service_zone"),
        settings.table_path("gold", "dim_zone"),
    )
    payments = read_delta(spark, settings.table_path("silver", "payment_types"))
    overwrite_table(
        payments.select(F.col("payment_type_id").alias("payment_type_key"), "payment_name"),
        settings.table_path("gold", "dim_payment_type"),
    )
    bounds = trips.agg(F.min("pickup_date").alias("lo"), F.max("pickup_date").alias("hi")).first()
    if bounds["lo"] is not None:
        days = spark.range(1).select(
            F.explode(
                F.sequence(F.lit(bounds["lo"]), F.lit(bounds["hi"]), F.expr("interval 1 day"))
            ).alias("date")
        )
        overwrite_table(
            days.select(
                (F.year("date") * 10000 + F.month("date") * 100 + F.dayofmonth("date"))
                .cast("int")
                .alias("date_key"),
                "date",
                F.year("date").alias("year"),
                F.month("date").alias("month"),
                F.dayofmonth("date").alias("day"),
                F.dayofweek("date").alias("day_of_week"),
                F.dayofweek("date").isin(1, 7).alias("is_weekend"),
            ),
            settings.table_path("gold", "dim_date"),
        )


def build_gold(spark: SparkSession, settings: Settings, batch: str) -> None:
    ctx = batch_context(batch, settings.late_arrival_days)
    trips_path = settings.table_path("silver", "trips")
    with stage_run(settings, "gold", batch, "all") as rec:
        if not is_delta(spark, trips_path):
            raise RuntimeError("silver trips not found; run the silver stage first")
        trips = read_delta(spark, trips_path)
        _build_dims(spark, settings, trips)

        # Recompute the whole affected window (batch month + late-arrival window): re-run safe.
        predicate = f"pickup_date >= '{ctx['late_start']}' AND pickup_date < '{ctx['batch_end']}'"
        window = trips.filter(
            (F.col("pickup_date") >= F.lit(ctx["late_start"]).cast("date"))
            & (F.col("pickup_date") < F.lit(ctx["batch_end"]).cast("date"))
        )
        fact = (
            window.groupBy("pickup_date", "pu_location_id", "payment_type_id")
            .agg(
                F.count(F.lit(1)).alias("trips"),
                F.sum(F.coalesce(F.col("passenger_count"), F.lit(0)))
                .cast("long")
                .alias("passengers"),
                F.sum(_dec("trip_distance")).alias("distance_miles"),
                F.sum(_dec("fare_amount")).alias("fare_amount"),
                F.sum(_dec("tip_amount")).alias("tip_amount"),
                F.sum(_dec("tolls_amount")).alias("tolls_amount"),
                F.sum(_dec("total_amount")).alias("total_amount"),
                F.sum(F.coalesce(F.col("trip_seconds"), F.lit(0)))
                .cast("long")
                .alias("trip_seconds"),
            )
            .persist()
        )
        write_replace_where(fact, settings.table_path("gold", "fact_trips_daily"), predicate)

        weather = read_delta(spark, settings.table_path("silver", "weather_daily")).select(
            F.col("weather_date").alias("pickup_date"), "temp_max_c", "temp_min_c", "precip_mm"
        )
        daily = (
            fact.groupBy("pickup_date")
            .agg(
                F.sum("trips").alias("trips"),
                F.sum("passengers").alias("passengers"),
                F.sum("distance_miles").alias("distance_miles"),
                F.sum("fare_amount").alias("fare_amount"),
                F.sum("tip_amount").alias("tip_amount"),
                F.sum("total_amount").alias("revenue"),
                F.sum("trip_seconds").alias("trip_seconds"),
            )
            .withColumn("avg_trip_minutes", F.round(F.col("trip_seconds") / F.col("trips") / 60, 2))
            .withColumn("tip_pct", F.round(F.col("tip_amount") / F.col("fare_amount") * 100, 2))
            .withColumn("is_weekend", F.dayofweek("pickup_date").isin(1, 7))
            .join(weather, "pickup_date", "left")
        )
        write_replace_where(daily, settings.table_path("gold", "daily_summary"), predicate)
        rec.rows_out = fact.count()
        record_lineage(
            settings, "gold", batch,
            ["silver_trips", "silver_zones", "silver_payment_types", "silver_weather_daily"],
            ["gold_dim_date", "gold_dim_zone", "gold_dim_payment_type",
             "gold_fact_trips_daily", "gold_daily_summary"],
        )  # fmt: skip
    spark.catalog.clearCache()
