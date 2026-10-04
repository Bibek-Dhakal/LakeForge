"""Monthly batch ids (YYYY-MM) and the window context used by quality rules and gold."""

from __future__ import annotations

import re
from datetime import date, timedelta

_MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def parse_month(batch: str) -> date:
    m = _MONTH_RE.match(batch)
    if not m:
        raise ValueError(f"invalid batch id {batch!r}; expected YYYY-MM")
    return date(int(m[1]), int(m[2]), 1)


def add_months(batch: str, n: int) -> str:
    d = parse_month(batch)
    total = d.year * 12 + (d.month - 1) + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def month_bounds(batch: str) -> tuple[date, date]:
    """Return (start inclusive, end exclusive)."""
    return parse_month(batch), parse_month(add_months(batch, 1))


def month_range(start: str, end: str) -> list[str]:
    if parse_month(start) > parse_month(end):
        raise ValueError(f"start {start} is after end {end}")
    out = [start]
    while out[-1] != end:
        out.append(add_months(out[-1], 1))
    return out


def batch_context(batch: str, late_days: int) -> dict[str, str]:
    start, end = month_bounds(batch)
    return {
        "batch_start": start.isoformat(),
        "batch_end": end.isoformat(),
        "late_start": (start - timedelta(days=late_days)).isoformat(),
    }
