from datetime import datetime

import pytest

pytest.importorskip("pyspark")

from lakeforge.quality import Rule, validate  # noqa: E402

pytestmark = pytest.mark.spark

SCHEMA = (
    "id long, amount double, zone long, _batch_id string, _source string, _ingested_at timestamp"
)
NOW = datetime(2024, 1, 1)


def _rows():
    good = [(i, 10.0, 1, "b", "s", NOW) for i in range(1, 7)]
    bad = [
        (None, 10.0, 1, "b", "s", NOW),  # id null
        (100, -5.0, 1, "b", "s", NOW),  # amount negative
        (101, 10.0, 99, "b", "s", NOW),  # unknown zone
        (102, -1.0, 98, "b", "s", NOW),  # two failures
    ]
    return good, bad


def test_seeded_bad_records_are_all_quarantined(spark):
    good, bad = _rows()
    df = spark.createDataFrame(good + bad, SCHEMA)
    refs = {"zones": spark.createDataFrame([(1,), (2,)], "location_id long")}
    rules = [
        Rule("id_not_null", "not_null", "id", "id required"),
        Rule("amount_range", "range", "amount", "amount < 0", {"min": 0, "max": 1000}),
        Rule("zone_exists", "referential", "zone", "unknown zone",
             {"ref_table": "zones", "ref_column": "location_id"}),
    ]  # fmt: skip
    valid, quarantine = validate(df, rules, {}, refs)

    assert df.count() == valid.count() + quarantine.count()  # conservation
    assert quarantine.count() == len(bad)  # recall == 1.0
    assert valid.count() == len(good)
    multi = quarantine.filter("id = 102").first()
    assert set(multi["_failed_rules"]) == {"amount_range", "zone_exists"}
    assert "amount_range" in multi["_reasons"]


def test_expression_rule_uses_batch_window(spark):
    df = spark.createDataFrame(
        [(1, datetime(2024, 1, 5)), (2, datetime(2023, 12, 28)), (3, datetime(2023, 6, 1))],
        "id long, ts timestamp",
    ).selectExpr(
        "*", "'b' as _batch_id", "'s' as _source", "cast('2024-01-01' as timestamp) as _ingested_at"
    )
    rule = Rule("window", "expression", description="outside window",
                params={"expr": "ts >= '{late_start}' AND ts < '{batch_end}'"})  # fmt: skip
    ctx = {"late_start": "2023-12-25", "batch_end": "2024-02-01"}
    valid, quarantine = validate(df, [rule], ctx)
    assert sorted(r["id"] for r in valid.collect()) == [1, 2]  # id 2 = accepted late arrival
    assert [r["_record"] for r in quarantine.collect()][0].count("2023-06-01") == 1
