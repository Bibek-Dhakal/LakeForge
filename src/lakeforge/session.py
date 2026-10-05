"""Local (or standalone-cluster) Spark session configured for Delta Lake."""

from __future__ import annotations

from .settings import Settings


def get_spark(settings: Settings, app: str = "lakeforge"):
    from delta import configure_spark_with_delta_pip
    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder.appName(app)
        .master(settings.spark_master)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"
        )
        .config("spark.sql.shuffle.partitions", str(settings.spark_shuffle_partitions))
        .config("spark.driver.memory", settings.spark_driver_memory)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.databricks.delta.schema.autoMerge.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.debug.maxToStringFields", "1000")
    )
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
