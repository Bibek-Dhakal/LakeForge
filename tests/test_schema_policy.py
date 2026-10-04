import pytest

from lakeforge.contracts import TAXI_TRIPS
from lakeforge.schema_policy import SchemaBreakingChange, diff_schema, enforce


def _incoming(**overrides):
    cols = dict(TAXI_TRIPS.columns)
    cols.update(overrides)
    return cols


def test_identical_schema_is_clean():
    diff = diff_schema(TAXI_TRIPS, dict(TAXI_TRIPS.columns))
    assert not diff.is_breaking and not diff.added and not diff.widened


def test_additive_column_is_allowed():
    diff = enforce(TAXI_TRIPS, _incoming(cbd_congestion_fee="double"))
    assert diff.added == {"cbd_congestion_fee": "double"}


def test_safe_widening_is_allowed():
    diff = enforce(TAXI_TRIPS, _incoming(vendorid="int", passenger_count="bigint"))
    assert set(diff.widened) == {"vendorid", "passenger_count"}


def test_unsafe_type_change_halts():
    with pytest.raises(SchemaBreakingChange):
        enforce(TAXI_TRIPS, _incoming(fare_amount="string"))


def test_missing_required_column_halts():
    cols = _incoming()
    del cols["total_amount"]
    with pytest.raises(SchemaBreakingChange):
        enforce(TAXI_TRIPS, cols)


def test_missing_optional_column_is_tolerated():
    cols = _incoming()
    del cols["airport_fee"]
    assert enforce(TAXI_TRIPS, cols).missing_optional == ["airport_fee"]
