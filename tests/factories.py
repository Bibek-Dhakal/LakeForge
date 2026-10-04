"""Synthetic sources written to the same shapes the real pipeline ingests (offline, no network)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from lakeforge.ingest.api import FILENAME
from lakeforge.ingest.database import (
    create_schema,
    insert_payment_types,
    insert_zones,
)
from lakeforge.ingest.files import taxi_filename
from lakeforge.ingest.landing import land
from lakeforge.settings import Settings


def trip(i: int, pickup: str = "2024-01-10 08:00:00", minutes: int = 15, **over) -> dict:
    start = pd.Timestamp(pickup) + pd.Timedelta(seconds=i)
    fare = over.pop("fare", 12.5)
    row = {
        "VendorID": 1,
        "tpep_pickup_datetime": start,
        "tpep_dropoff_datetime": start + pd.Timedelta(minutes=minutes),
        "passenger_count": 1.0,
        "trip_distance": 2.5,
        "RatecodeID": 1.0,
        "store_and_fwd_flag": "N",
        "PULocationID": 1,
        "DOLocationID": 2,
        "payment_type": 1,
        "fare_amount": fare,
        "extra": 0.5,
        "mta_tax": 0.5,
        "tip_amount": 2.0,
        "tolls_amount": 0.0,
        "improvement_surcharge": 1.0,
        "total_amount": fare + 4.0,
        "congestion_surcharge": 2.5,
        "Airport_fee": 0.0,
    }
    row.update(over)
    return row


def write_taxi(settings: Settings, batch: str, rows: list[dict]) -> Path:
    folder = Path(settings.taxi_base_url)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / taxi_filename(batch)
    pd.DataFrame(rows).to_parquet(path, index=False, coerce_timestamps="us")
    return path


def seed_reference(settings: Settings) -> None:
    settings.source_db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(settings.source_db_path)
    try:
        create_schema(con)
        insert_zones(con, [(i, "Manhattan", f"Zone {i}", "Yellow Zone") for i in range(1, 6)])
        insert_payment_types(con, [(1, "Credit card"), (2, "Cash")])
        con.commit()
    finally:
        con.close()


def land_weather(settings: Settings, batch: str, days: list[str]) -> None:
    payload = {
        "daily": {
            "time": days,
            "temperature_2m_max": [5.0] * len(days),
            "temperature_2m_min": [-1.0] * len(days),
            "precipitation_sum": [0.5] * len(days),
        }
    }
    land(settings, "api", batch, {FILENAME: lambda dest: dest.write_text(json.dumps(payload))})
