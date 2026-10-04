"""Table catalog: registry used by serving, lineage docs and the generated data catalog."""

from __future__ import annotations

from dataclasses import dataclass

from deltalake import DeltaTable

from .settings import Settings


@dataclass(frozen=True)
class TableInfo:
    layer: str
    name: str
    description: str
    upstream: tuple[str, ...]


TABLES: dict[str, TableInfo] = {
    "bronze_taxi_trips": TableInfo(
        "bronze",
        "taxi_trips",
        "Raw yellow-taxi trips; append-only per batch, duplicates kept.",
        ("landing_files",),
    ),
    "bronze_weather_daily": TableInfo(
        "bronze", "weather_daily", "Raw daily weather from Open-Meteo.", ("landing_api",)
    ),
    "bronze_zones": TableInfo("bronze", "zones", "Taxi zones snapshot per batch.", ("landing_db",)),
    "bronze_payment_types": TableInfo(
        "bronze", "payment_types", "Payment types snapshot per batch.", ("landing_db",)
    ),
    "quarantine_taxi_trips": TableInfo(
        "quarantine",
        "taxi_trips",
        "Trips failing quality rules (rule + reason + batch).",
        ("bronze_taxi_trips",),
    ),
    "quarantine_weather_daily": TableInfo(
        "quarantine", "weather_daily", "Weather rows failing rules.", ("bronze_weather_daily",)
    ),
    "quarantine_zones": TableInfo(
        "quarantine", "zones", "Zone rows failing rules.", ("bronze_zones",)
    ),
    "quarantine_payment_types": TableInfo(
        "quarantine", "payment_types", "Payment-type rows failing rules.", ("bronze_payment_types",)
    ),
    "silver_zones": TableInfo(
        "silver", "zones", "Conformed taxi zones (MERGE on location_id).", ("bronze_zones",)
    ),
    "silver_payment_types": TableInfo(
        "silver", "payment_types", "Conformed payment types.", ("bronze_payment_types",)
    ),
    "silver_weather_daily": TableInfo(
        "silver",
        "weather_daily",
        "Cleaned daily weather (MERGE on weather_date).",
        ("bronze_weather_daily",),
    ),
    "silver_trips": TableInfo(
        "silver",
        "trips",
        "Cleaned, deduplicated trips (MERGE on trip_id); late arrivals flagged.",
        ("bronze_taxi_trips", "silver_zones", "silver_payment_types"),
    ),
    "gold_dim_date": TableInfo("gold", "dim_date", "Date dimension.", ("silver_trips",)),
    "gold_dim_zone": TableInfo("gold", "dim_zone", "Zone dimension.", ("silver_zones",)),
    "gold_dim_payment_type": TableInfo(
        "gold", "dim_payment_type", "Payment type dimension.", ("silver_payment_types",)
    ),
    "gold_fact_trips_daily": TableInfo(
        "gold",
        "fact_trips_daily",
        "Fact: trips by pickup date x pickup zone x payment type.",
        ("silver_trips",),
    ),
    "gold_daily_summary": TableInfo(
        "gold",
        "daily_summary",
        "Daily KPIs joined with weather; ML-ready feature table.",
        ("gold_fact_trips_daily", "silver_weather_daily"),
    ),
}


def table_path(settings: Settings, name: str) -> str:
    info = TABLES[name]
    return settings.table_path(info.layer, info.name)


def mermaid_lineage() -> str:
    lines = ["graph LR"]
    for name, info in TABLES.items():
        for up in info.upstream:
            lines.append(f"    {up} --> {name}")
    return "\n".join(lines)


def render_markdown(settings: Settings) -> str:
    out = ["# LakeForge data catalog", "", "Generated per pipeline run.", ""]
    for name, info in TABLES.items():
        out += [
            f"## {name}",
            "",
            f"- **Layer:** {info.layer}",
            f"- **Description:** {info.description}",
        ]
        out.append("- **Upstream:** " + (", ".join(info.upstream) or "-"))
        path = settings.table_path(info.layer, info.name)
        if DeltaTable.is_deltatable(path):
            schema = DeltaTable(path).to_pyarrow_dataset().schema
            out += ["", "| Column | Type |", "|---|---|"]
            out += [f"| {n} | {t} |" for n, t in zip(schema.names, schema.types, strict=True)]
        else:
            out.append("- **Status:** not materialised yet")
        out.append("")
    out += ["## Lineage", "", "```mermaid", mermaid_lineage(), "```", ""]
    return "\n".join(out)


def write_catalog(settings: Settings) -> None:
    settings.meta_dir.mkdir(parents=True, exist_ok=True)
    (settings.meta_dir / "catalog.md").write_text(render_markdown(settings), encoding="utf-8")
    (settings.meta_dir / "lineage.mmd").write_text(mermaid_lineage(), encoding="utf-8")
