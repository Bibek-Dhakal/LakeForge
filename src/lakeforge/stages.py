"""Pipeline stage names shared by the CLI, Airflow DAG and orchestration code."""

from __future__ import annotations

INGEST_STAGES = ("ingest_files", "ingest_api", "ingest_db")
BRONZE_STAGES = ("bronze_files", "bronze_api", "bronze_db")
PROCESS_STAGES = (*BRONZE_STAGES, "silver", "gold", "catalog")
ALL_STAGES = (*INGEST_STAGES, *PROCESS_STAGES)
SPARK_STAGES = (*BRONZE_STAGES, "silver", "gold")
