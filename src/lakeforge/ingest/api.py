"""API source: Open-Meteo historical daily weather (no API key required)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from ..batches import month_bounds
from ..lineage import record_lineage
from ..metrics import stage_run
from ..settings import Settings
from .landing import LandingResult, land
from .net import get_text

SOURCE = "api"
FILENAME = "weather.json"
DAILY_FIELDS = ("temperature_2m_max", "temperature_2m_min", "precipitation_sum")


def fetch_weather(settings: Settings, batch: str, dest: Path) -> None:
    start, end = month_bounds(batch)
    params = {
        "latitude": settings.weather_lat,
        "longitude": settings.weather_lon,
        "start_date": start.isoformat(),
        "end_date": (end - timedelta(days=1)).isoformat(),
        "daily": ",".join(DAILY_FIELDS),
        "timezone": settings.weather_timezone,
    }
    dest.write_text(get_text(settings.weather_url, settings, params=params), encoding="utf-8")


def rows_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    daily = payload.get("daily") or {}
    days = daily.get("time")
    if not days:
        raise ValueError("weather payload has no daily.time")
    rows = []
    for i, day in enumerate(days):
        row: dict[str, Any] = {"date": day}
        for name in DAILY_FIELDS:
            values = daily.get(name) or []
            value = values[i] if i < len(values) else None
            row[name] = float(value) if value is not None else None
        rows.append(row)
    return rows


def ingest_weather(settings: Settings, batch: str) -> LandingResult:
    with stage_run(settings, "ingest_api", batch) as rec:
        result = land(
            settings, SOURCE, batch, {FILENAME: lambda dest: fetch_weather(settings, batch, dest)}
        )
        rec.extra["bytes"] = sum(f["bytes"] for f in result.manifest["files"])
        record_lineage(settings, "ingest_api", batch, [settings.weather_url], ["landing_api"])
    return result
