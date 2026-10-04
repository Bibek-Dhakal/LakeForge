"""File source: NYC TLC yellow-taxi monthly parquet files."""

from __future__ import annotations

from ..lineage import record_lineage
from ..metrics import stage_run
from ..settings import Settings
from .landing import LandingResult, land
from .net import download

SOURCE = "files"


def taxi_filename(batch: str) -> str:
    return f"yellow_tripdata_{batch}.parquet"


def ingest_taxi(settings: Settings, batch: str) -> LandingResult:
    name = taxi_filename(batch)
    src = f"{settings.taxi_base_url.rstrip('/')}/{name}"
    with stage_run(settings, "ingest_files", batch) as rec:
        result = land(settings, SOURCE, batch, {name: lambda dest: download(src, dest, settings)})
        rec.extra["bytes"] = sum(f["bytes"] for f in result.manifest["files"])
        record_lineage(settings, "ingest_files", batch, [src], ["landing_files"])
    return result
