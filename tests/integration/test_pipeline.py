import pytest

pytest.importorskip("pyspark")

from factories import land_weather, seed_reference, trip, write_taxi  # noqa: E402
from lakeforge.delta_io import read_delta  # noqa: E402
from lakeforge.evaluation import fingerprint  # noqa: E402
from lakeforge.metrics import read_metrics  # noqa: E402
from lakeforge.pipeline import run_batch  # noqa: E402
from lakeforge.schema_policy import SchemaBreakingChange  # noqa: E402
from lakeforge.stages import ALL_STAGES, PROCESS_STAGES  # noqa: E402

pytestmark = pytest.mark.spark
BATCH = "2024-01"


def _january_days():
    return [f"2024-01-{d:02d}" for d in range(1, 32)]


def _build_sources(env):
    good = [trip(i) for i in range(10)]
    rows = (
        good
        + good[:2]  # exact duplicates
        + [trip(200, fare=-5.0)]  # negative fare
        + [trip(201, PULocationID=999)]  # unknown zone
        + [trip(202, pickup="2023-12-28 10:00:00")]  # late arrival inside window
        + [trip(203, pickup="2023-06-01 10:00:00")]  # far outside window
    )
    write_taxi(env, BATCH, rows)
    seed_reference(env)
    land_weather(env, BATCH, _january_days())
    return len(rows)


def test_end_to_end_quarantine_dedupe_late_and_conservation(spark, env):
    total_in = _build_sources(env)
    run_batch(env, BATCH, spark, ALL_STAGES)

    silver = read_delta(spark, env.table_path("silver", "trips"))
    quarantine = read_delta(spark, env.table_path("quarantine", "taxi_trips"))
    assert silver.count() == 11  # 10 good (dupes removed) + 1 late arrival
    assert silver.filter("is_late_arrival").count() == 1
    assert quarantine.count() == 3  # negative fare, unknown zone, outside window

    rec = [
        r for r in read_metrics(env)
        if r["stage"] == "silver" and r["table"] == "trips"
    ][-1]  # fmt: skip
    assert rec["rows_in"] == total_in
    assert rec["rows_in"] == rec["rows_valid"] + rec["rows_quarantined"]

    daily = read_delta(spark, env.table_path("gold", "daily_summary"))
    assert daily.filter("precip_mm is not null").count() > 0  # weather joined


def test_rerun_produces_identical_state(spark, env):
    _build_sources(env)
    run_batch(env, BATCH, spark, ALL_STAGES)
    first = fingerprint(spark, env)
    run_batch(env, BATCH, spark, PROCESS_STAGES)
    run_batch(env, BATCH, spark, PROCESS_STAGES)
    assert fingerprint(spark, env) == first


def test_additive_schema_change_is_absorbed(spark, env):
    seed_reference(env)
    land_weather(env, BATCH, _january_days())
    rows = [trip(i, cbd_congestion_fee=0.75) for i in range(5)]
    write_taxi(env, BATCH, rows)
    run_batch(env, BATCH, spark, ALL_STAGES)
    bronze = read_delta(spark, env.table_path("bronze", "taxi_trips"))
    assert "cbd_congestion_fee" in bronze.columns
    assert read_delta(spark, env.table_path("silver", "trips")).count() == 5


def test_breaking_schema_change_halts_before_writing(spark, env):
    seed_reference(env)
    rows = [{**trip(i), "fare_amount": "twelve"} for i in range(3)]
    write_taxi(env, BATCH, rows)
    run_batch(env, BATCH, spark, ("ingest_files",))
    with pytest.raises(SchemaBreakingChange):
        run_batch(env, BATCH, spark, ("bronze_files",))
    failed = [r for r in read_metrics(env) if r["stage"] == "bronze_files"]
    assert failed and failed[-1]["status"] == "failed"
