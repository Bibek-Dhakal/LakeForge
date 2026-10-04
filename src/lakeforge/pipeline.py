"""Orchestration entry points shared by the CLI and Airflow: stages, batches, backfills."""

from __future__ import annotations

import logging

from pyspark.sql import SparkSession

from . import bronze, gold, silver
from .batches import month_range
from .catalog import write_catalog
from .ingest import api, database, files
from .session import get_spark
from .settings import Settings
from .stages import ALL_STAGES, INGEST_STAGES, SPARK_STAGES

log = logging.getLogger(__name__)


def run_stage(
    settings: Settings, stage: str, batch: str, spark: SparkSession | None = None
) -> None:
    if stage == "ingest_files":
        files.ingest_taxi(settings, batch)
    elif stage == "ingest_api":
        api.ingest_weather(settings, batch)
    elif stage == "ingest_db":
        database.ingest_reference(settings, batch)
    elif stage == "catalog":
        write_catalog(settings)
    else:
        spark = spark or get_spark(settings)
        if stage == "bronze_files":
            bronze.load_taxi(spark, settings, batch)
        elif stage == "bronze_api":
            bronze.load_weather(spark, settings, batch)
        elif stage == "bronze_db":
            bronze.load_reference(spark, settings, batch)
        elif stage == "silver":
            silver.run_silver(spark, settings, batch)
        elif stage == "gold":
            gold.build_gold(spark, settings, batch)
        else:
            raise ValueError(f"unknown stage {stage!r}")


def run_batch(
    settings: Settings,
    batch: str,
    spark: SparkSession | None = None,
    stages: tuple[str, ...] = ALL_STAGES,
) -> None:
    if spark is None and any(s in SPARK_STAGES for s in stages):
        spark = get_spark(settings)
    for stage in stages:
        log.info("batch=%s stage=%s", batch, stage)
        run_stage(settings, stage, batch, spark)


def run_range(
    settings: Settings,
    start: str,
    end: str,
    stages: tuple[str, ...] = ALL_STAGES,
    spark: SparkSession | None = None,
) -> list[str]:
    """Parameterised backfill: process every month in [start, end] in order."""
    if spark is None and any(s in SPARK_STAGES for s in stages):
        spark = get_spark(settings)
    batches = month_range(start, end)
    for batch in batches:
        run_batch(settings, batch, spark, stages)
    return batches


__all__ = ["INGEST_STAGES", "run_batch", "run_range", "run_stage"]
