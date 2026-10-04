"""Monthly LakeForge DAG. Backfill: `airflow dags backfill -s 2024-01-01 -e 2024-03-31 lakeforge_monthly`."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

log = logging.getLogger(__name__)
MONTH = "{{ data_interval_start.strftime('%Y-%m') }}"


def _alert(context) -> None:
    ti = context["task_instance"]
    log.error("ALERT: task %s failed for run %s", ti.task_id, context["run_id"])


default_args = {
    "owner": "lakeforge",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(hours=2),
    "on_failure_callback": _alert,
}

with DAG(
    dag_id="lakeforge_monthly",
    description="Raw -> bronze -> silver -> gold for one month (idempotent, re-runnable)",
    start_date=datetime(2024, 1, 1),
    schedule="@monthly",
    catchup=True,
    max_active_runs=1,
    default_args=default_args,
    tags=["lakeforge", "lakehouse"],
) as dag:

    def stage(name: str) -> BashOperator:
        return BashOperator(task_id=name, bash_command=f"lakeforge stage {name} --month {MONTH}")

    ingest_files, ingest_api, ingest_db = (
        stage(n) for n in ("ingest_files", "ingest_api", "ingest_db")
    )
    bronze_files, bronze_api, bronze_db = (
        stage(n) for n in ("bronze_files", "bronze_api", "bronze_db")
    )
    silver, gold, catalog = stage("silver"), stage("gold"), stage("catalog")

    ingest_files >> bronze_files
    ingest_api >> bronze_api
    ingest_db >> bronze_db
    [bronze_files, bronze_api, bronze_db] >> silver >> gold >> catalog
