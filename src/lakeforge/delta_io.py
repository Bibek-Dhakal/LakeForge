"""Idempotent Delta write primitives: replace-by-predicate, overwrite and MERGE."""

from __future__ import annotations

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession


def is_delta(spark: SparkSession, path: str) -> bool:
    return DeltaTable.isDeltaTable(spark, path)


def read_delta(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.format("delta").load(path)


def write_replace_where(
    df: DataFrame,
    path: str,
    predicate: str,
    partition_by: list[str] | None = None,
    merge_schema: bool = False,
) -> None:
    """Atomically replace the rows matching `predicate` with `df` (re-run safe)."""
    writer = df.write.format("delta")
    if merge_schema:
        writer = writer.option("mergeSchema", "true")
    if is_delta(df.sparkSession, path):
        writer.mode("overwrite").option("replaceWhere", predicate).save(path)
    else:
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        writer.mode("overwrite").save(path)


def overwrite_table(df: DataFrame, path: str) -> None:
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(path)


def merge_into(
    spark: SparkSession,
    source: DataFrame,
    path: str,
    keys: list[str],
    update_condition: str | None = None,
    partition_by: list[str] | None = None,
) -> None:
    """Upsert `source` (must be unique on `keys`) into the Delta table at `path`."""
    if not is_delta(spark, path):
        writer = source.write.format("delta")
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        writer.mode("overwrite").save(path)
        return
    condition = " AND ".join(f"t.{k} = s.{k}" for k in keys)
    merge = DeltaTable.forPath(spark, path).alias("t").merge(source.alias("s"), condition)
    merge = (
        merge.whenMatchedUpdateAll(condition=update_condition)
        if update_condition
        else merge.whenMatchedUpdateAll()
    )
    merge.whenNotMatchedInsertAll().execute()
