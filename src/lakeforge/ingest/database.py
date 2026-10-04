"""Relational source: a SQLite reference database extracted as-of the end of each batch month."""

from __future__ import annotations

import csv
import io
import sqlite3
from pathlib import Path

import pandas as pd

from ..batches import month_bounds
from ..lineage import record_lineage
from ..metrics import stage_run
from ..settings import Settings
from .landing import LandingResult, land
from .net import get_text

SOURCE = "db"
TABLES = ("zones", "payment_types")
SEED_UPDATED_AT = "2000-01-01T00:00:00"
PAYMENT_TYPES = [
    (0, "Flex fare trip"),
    (1, "Credit card"),
    (2, "Cash"),
    (3, "No charge"),
    (4, "Dispute"),
    (5, "Unknown"),
    (6, "Voided trip"),
]
_DDL = (
    """CREATE TABLE IF NOT EXISTS zones (
        location_id INTEGER PRIMARY KEY, borough TEXT, zone TEXT,
        service_zone TEXT, updated_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS payment_types (
        payment_type_id INTEGER PRIMARY KEY, payment_name TEXT, updated_at TEXT NOT NULL)""",
)


def create_schema(con: sqlite3.Connection) -> None:
    for ddl in _DDL:
        con.execute(ddl)


def insert_zones(con: sqlite3.Connection, rows: list[tuple]) -> None:
    """rows: (location_id, borough, zone, service_zone)."""
    con.executemany(
        "INSERT OR REPLACE INTO zones VALUES (?, ?, ?, ?, ?)",
        [(*r, SEED_UPDATED_AT) for r in rows],
    )


def insert_payment_types(con: sqlite3.Connection, rows: list[tuple]) -> None:
    """rows: (payment_type_id, payment_name)."""
    con.executemany(
        "INSERT OR REPLACE INTO payment_types VALUES (?, ?, ?)",
        [(*r, SEED_UPDATED_AT) for r in rows],
    )


def seed_source_db(settings: Settings) -> int:
    """Create the source DB from the public TLC zone lookup. Returns the zone count."""
    text = get_text(settings.zones_url, settings)
    zones = [
        (int(r["LocationID"]), r["Borough"], r["Zone"], r["service_zone"])
        for r in csv.DictReader(io.StringIO(text))
    ]
    settings.source_db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(settings.source_db_path)
    try:
        create_schema(con)
        insert_zones(con, zones)
        insert_payment_types(con, PAYMENT_TYPES)
        con.commit()
    finally:
        con.close()
    return len(zones)


def extract_table(settings: Settings, table: str, as_of_exclusive: str, dest: Path) -> None:
    if table not in TABLES:
        raise ValueError(f"table {table!r} is not an allowed source table")
    con = sqlite3.connect(settings.source_db_path)
    try:
        df = pd.read_sql_query(
            f"SELECT * FROM {table} WHERE updated_at < ? ORDER BY 1",  # noqa: S608 (whitelisted)
            con,
            params=(as_of_exclusive,),
        )
    finally:
        con.close()
    df.to_parquet(dest, index=False)


def ingest_reference(settings: Settings, batch: str) -> LandingResult:
    _, end = month_bounds(batch)
    cutoff = end.isoformat()
    fetchers = {
        f"{t}.parquet": (lambda dest, t=t: extract_table(settings, t, cutoff, dest)) for t in TABLES
    }
    with stage_run(settings, "ingest_db", batch) as rec:
        result = land(settings, SOURCE, batch, fetchers)
        rec.extra["as_of_exclusive"] = cutoff
        record_lineage(
            settings, "ingest_db", batch, [f"sqlite:{t}" for t in TABLES], ["landing_db"]
        )
    return result
