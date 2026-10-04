"""Role-based access: API keys -> roles -> allowed tables, plus a read-only SQL guard."""

from __future__ import annotations

import hmac
import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Principal:
    role: str
    tables: frozenset[str]


def parse_api_keys(raw: str) -> dict[str, str]:
    """Parse 'key:role,key:role' into {key: role}."""
    keys: dict[str, str] = {}
    for item in (part.strip() for part in raw.split(",")):
        key, _, role = item.partition(":")
        if key and role:
            keys[key] = role
    return keys


def load_policy(path: Path | str) -> dict[str, frozenset[str]]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return {role: frozenset(tables) for role, tables in data["roles"].items()}


def authenticate(
    presented: str | None, keys: dict[str, str], policy: dict[str, frozenset[str]]
) -> Principal | None:
    if not presented:
        return None
    match: str | None = None
    for key, role in keys.items():
        if hmac.compare_digest(key.encode(), presented.encode()):
            match = role
    if match is None or match not in policy:
        return None
    return Principal(match, policy[match])


_FORBIDDEN = re.compile(
    r"\b(attach|detach|copy|export|import|install|load|pragma|create|drop|alter|insert|update|"
    r"delete|truncate|call|read_csv\w*|read_parquet|read_json\w*|read_text|glob|parquet_scan|"
    r"delta_scan|iceberg_scan|httpfs)\b",
    re.IGNORECASE,
)


def check_sql(sql: str) -> str:
    """Return a cleaned single SELECT/WITH statement or raise ValueError."""
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise ValueError("empty query")
    if ";" in cleaned:
        raise ValueError("multiple statements are not allowed")
    if not re.match(r"(?is)^(select|with)\b", cleaned):
        raise ValueError("only SELECT queries are allowed")
    if _FORBIDDEN.search(cleaned):
        raise ValueError("query contains a forbidden keyword")
    return cleaned
