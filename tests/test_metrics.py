from datetime import datetime, timezone

from lakeforge.metrics import render_prometheus


def _rec(stage, finished, status="success", **kw):
    base = {
        "stage": stage,
        "batch_id": "2024-01",
        "table": "trips",
        "status": status,
        "duration_s": 1.5,
        "finished_at": finished,
        "rows_in": 10,
        "rows_valid": 8,
        "rows_quarantined": 2,
    }
    base.update(kw)
    return base


def test_quality_ratio_and_freshness_ok():
    now = datetime(2024, 2, 1, 12, tzinfo=timezone.utc)
    text = render_prometheus([_rec("gold", "2024-02-01T06:00:00+00:00")], 26, now=now)
    assert "lakeforge_quality_pass_ratio" in text and "0.8" in text
    assert "lakeforge_freshness_slo_breached{} 0" in text


def test_freshness_breach_and_failure_flag():
    now = datetime(2024, 2, 10, tzinfo=timezone.utc)
    records = [
        _rec("gold", "2024-02-01T06:00:00+00:00"),
        _rec("silver", "2024-02-09T06:00:00+00:00", status="failed"),
    ]
    text = render_prometheus(records, 26, now=now)
    assert "lakeforge_freshness_slo_breached{} 1" in text
    assert 'lakeforge_stage_failed{stage="silver"' in text and "} 1" in text


def test_no_gold_run_counts_as_breach():
    assert "lakeforge_freshness_slo_breached{} 1" in render_prometheus([], 26)
