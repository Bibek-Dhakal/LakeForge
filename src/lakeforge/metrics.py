"""Per-stage run records (JSON files) plus Prometheus text rendering. No Spark dependency."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .settings import Settings

log = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


@dataclass
class StageRecord:
    stage: str
    batch_id: str
    table: str | None = None
    status: str = "running"
    rows_in: int | None = None
    rows_valid: int | None = None
    rows_quarantined: int | None = None
    rows_out: int | None = None
    duration_s: float = 0.0
    started_at: str = ""
    finished_at: str = ""
    run_id: str = ""
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _write(settings: Settings, rec: StageRecord) -> None:
    out = settings.meta_dir / "metrics"
    out.mkdir(parents=True, exist_ok=True)
    stamp = rec.finished_at.replace(":", "")
    name = f"{stamp}__{rec.stage}__{rec.table or 'all'}__{rec.batch_id}__{rec.run_id}.json"
    (out / name).write_text(json.dumps(asdict(rec), indent=2, default=str))


@contextmanager
def stage_run(
    settings: Settings, stage: str, batch_id: str, table: str | None = None
) -> Iterator[StageRecord]:
    rec = StageRecord(stage=stage, batch_id=batch_id, table=table, run_id=uuid.uuid4().hex[:12])
    rec.started_at = iso(utcnow())
    t0 = time.monotonic()

    def finish(status: str) -> None:
        rec.status = status
        rec.duration_s = round(time.monotonic() - t0, 3)
        rec.finished_at = iso(utcnow())
        _write(settings, rec)

    try:
        yield rec
    except Exception as exc:
        rec.error = f"{type(exc).__name__}: {exc}"[:500]
        finish("failed")
        log.error("ALERT stage=%s table=%s batch=%s failed: %s", stage, table, batch_id, rec.error)
        raise
    else:
        finish("success")
        log.info("stage=%s table=%s batch=%s ok in %.1fs", stage, table, batch_id, rec.duration_s)


def read_metrics(settings: Settings) -> list[dict[str, Any]]:
    folder = settings.meta_dir / "metrics"
    if not folder.exists():
        return []
    records = []
    for path in sorted(folder.glob("*.json")):
        try:
            records.append(json.loads(path.read_text()))
        except json.JSONDecodeError:
            continue
    return records


def _labels(r: dict[str, Any]) -> str:
    return f'stage="{r["stage"]}",table="{r.get("table") or "all"}",batch="{r["batch_id"]}"'


def render_prometheus(
    records: list[dict[str, Any]], slo_hours: float, now: datetime | None = None
) -> str:
    now = now or utcnow()
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for r in records:
        key = (r["stage"], r.get("table") or "all", r["batch_id"])
        if key not in latest or r["finished_at"] >= latest[key]["finished_at"]:
            latest[key] = r

    lines: list[str] = []

    def emit(name: str, help_: str, rows: list[tuple[str, float]]) -> None:
        lines.append(f"# HELP {name} {help_}")
        lines.append(f"# TYPE {name} gauge")
        lines.extend(f"{name}{{{lbl}}} {val}" for lbl, val in rows)

    ok = [r for r in latest.values() if r["status"] == "success"]
    emit(
        "lakeforge_stage_last_success_timestamp_seconds",
        "Unix time of the last successful run",
        [(_labels(r), datetime.fromisoformat(r["finished_at"]).timestamp()) for r in ok],
    )
    emit(
        "lakeforge_stage_duration_seconds",
        "Duration of the latest run",
        [(_labels(r), r["duration_s"]) for r in latest.values()],
    )
    emit(
        "lakeforge_stage_failed",
        "1 if the latest run of the stage failed",
        [(_labels(r), 1 if r["status"] == "failed" else 0) for r in latest.values()],
    )
    emit(
        "lakeforge_rows_in",
        "Rows entering validation",
        [(_labels(r), r["rows_in"]) for r in latest.values() if r.get("rows_in") is not None],
    )
    emit(
        "lakeforge_rows_quarantined",
        "Rows quarantined",
        [
            (_labels(r), r["rows_quarantined"])
            for r in latest.values()
            if r.get("rows_quarantined") is not None
        ],
    )
    emit(
        "lakeforge_quality_pass_ratio",
        "valid rows / input rows",
        [
            (_labels(r), round(r["rows_valid"] / r["rows_in"], 6))
            for r in latest.values()
            if r.get("rows_in") and r.get("rows_valid") is not None
        ],
    )

    gold_ok = [
        datetime.fromisoformat(r["finished_at"])
        for r in records
        if r["stage"] == "gold" and r["status"] == "success"
    ]
    if gold_ok:
        age = (now - max(gold_ok)).total_seconds()
        emit("lakeforge_freshness_seconds", "Seconds since last successful gold build", [("", age)])
        breached = 1 if age > slo_hours * 3600 else 0
    else:
        breached = 1
    emit("lakeforge_freshness_slo_breached", "1 if freshness SLO is breached", [("", breached)])
    return "\n".join(lines) + "\n"
