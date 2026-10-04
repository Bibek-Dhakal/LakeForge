import pytest

from lakeforge.batches import add_months, batch_context, month_bounds, month_range


def test_month_range_crosses_year():
    assert month_range("2023-11", "2024-02") == ["2023-11", "2023-12", "2024-01", "2024-02"]


def test_add_months_negative():
    assert add_months("2024-01", -1) == "2023-12"


def test_bounds_are_half_open():
    start, end = month_bounds("2024-02")
    assert (start.isoformat(), end.isoformat()) == ("2024-02-01", "2024-03-01")


def test_context_has_late_window():
    ctx = batch_context("2024-01", 7)
    assert ctx == {
        "batch_start": "2024-01-01",
        "batch_end": "2024-02-01",
        "late_start": "2023-12-25",
    }


def test_invalid_batch_rejected():
    with pytest.raises(ValueError):
        month_bounds("2024-13")


def test_reversed_range_rejected():
    with pytest.raises(ValueError):
        month_range("2024-03", "2024-01")
