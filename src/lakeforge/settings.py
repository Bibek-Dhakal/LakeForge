"""Single source of truth for configuration. Everything comes from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv


def _get(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    lake_root: Path
    source_db_path: Path
    config_dir: Path
    taxi_base_url: str
    zones_url: str
    weather_url: str
    weather_lat: float
    weather_lon: float
    weather_timezone: str
    late_arrival_days: int
    freshness_slo_hours: float
    spark_master: str
    spark_driver_memory: str
    spark_shuffle_partitions: int
    http_timeout_s: int
    http_retries: int
    api_keys: str
    max_query_rows: int
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        return cls(
            lake_root=Path(_get("LAKE_ROOT", "./data/lake")).resolve(),
            source_db_path=Path(_get("SOURCE_DB_PATH", "./data/source/reference.db")).resolve(),
            config_dir=Path(_get("CONFIG_DIR", "./config")).resolve(),
            taxi_base_url=_get("TAXI_BASE_URL", "https://d37ci6vzurychx.cloudfront.net/trip-data"),
            zones_url=_get(
                "ZONES_URL", "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
            ),
            weather_url=_get("WEATHER_URL", "https://archive-api.open-meteo.com/v1/archive"),
            weather_lat=float(_get("WEATHER_LAT", "40.7128")),
            weather_lon=float(_get("WEATHER_LON", "-74.0060")),
            weather_timezone=_get("WEATHER_TIMEZONE", "America/New_York"),
            late_arrival_days=int(_get("LATE_ARRIVAL_DAYS", "7")),
            freshness_slo_hours=float(_get("FRESHNESS_SLO_HOURS", "26")),
            spark_master=_get("SPARK_MASTER", "local[*]"),
            spark_driver_memory=_get("SPARK_DRIVER_MEMORY", "4g"),
            spark_shuffle_partitions=int(_get("SPARK_SHUFFLE_PARTITIONS", "8")),
            http_timeout_s=int(_get("HTTP_TIMEOUT_S", "60")),
            http_retries=int(_get("HTTP_RETRIES", "4")),
            api_keys=_get("API_KEYS", ""),
            max_query_rows=int(_get("MAX_QUERY_ROWS", "10000")),
            log_level=_get("LOG_LEVEL", "INFO"),
        )

    def with_lake_root(self, root: Path | str) -> Settings:
        return replace(self, lake_root=Path(root).resolve())

    # ---- derived locations -------------------------------------------------
    @property
    def meta_dir(self) -> Path:
        return self.lake_root / "meta"

    @property
    def rules_file(self) -> Path:
        return self.config_dir / "quality_rules.yaml"

    @property
    def policy_file(self) -> Path:
        return self.config_dir / "access_policy.yaml"

    def landing_dir(self, source: str, batch_id: str) -> Path:
        return self.lake_root / "landing" / source / batch_id

    def table_path(self, layer: str, name: str) -> str:
        return (self.lake_root / layer / name).as_posix()
