"""Schema evolution policy. Pure Python so it is unit-testable without Spark.

Policy:
  * additive columns            -> allowed (table evolves via mergeSchema)
  * safe widening (int->bigint) -> allowed (values are cast to the contract type)
  * missing optional column     -> allowed (filled with NULL)
  * missing required column, or any non-widening type change -> BREAKING: halt + alert
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import Contract

_NUMERIC_RANK = {
    "tinyint": 1,
    "smallint": 2,
    "int": 3,
    "integer": 3,
    "bigint": 4,
    "float": 5,
    "double": 6,
    "decimal": 6,
}
_TEMPORAL_OK = {
    ("timestamp_ntz", "timestamp"),
    ("timestamp", "timestamp_ntz"),
    ("date", "timestamp"),
    ("date", "timestamp_ntz"),
}


class SchemaBreakingChange(RuntimeError):
    """Raised when incoming data violates the schema contract in a non-evolvable way."""


@dataclass
class SchemaDiff:
    added: dict[str, str] = field(default_factory=dict)
    missing_optional: list[str] = field(default_factory=list)
    widened: dict[str, tuple[str, str]] = field(default_factory=dict)
    breaking: list[str] = field(default_factory=list)

    @property
    def is_breaking(self) -> bool:
        return bool(self.breaking)


def base_type(t: str) -> str:
    return t.lower().split("(")[0].strip()


def can_conform(incoming: str, target: str) -> bool:
    i, t = base_type(incoming), base_type(target)
    if i == t:
        return True
    if i in _NUMERIC_RANK and t in _NUMERIC_RANK:
        return _NUMERIC_RANK[i] <= _NUMERIC_RANK[t]
    return (i, t) in _TEMPORAL_OK


def diff_schema(contract: Contract, incoming: dict[str, str]) -> SchemaDiff:
    diff = SchemaDiff()
    diff.added = {c: t for c, t in incoming.items() if c not in contract.columns}
    for col, target in contract.columns.items():
        if col not in incoming:
            if col in contract.required:
                diff.breaking.append(f"{col}: required column missing")
            else:
                diff.missing_optional.append(col)
            continue
        got = incoming[col]
        if base_type(got) == base_type(target):
            continue
        if can_conform(got, target):
            diff.widened[col] = (got, target)
        else:
            diff.breaking.append(f"{col}: {got} -> {target} is not a safe widening")
    return diff


def enforce(contract: Contract, incoming: dict[str, str]) -> SchemaDiff:
    diff = diff_schema(contract, incoming)
    if diff.is_breaking:
        raise SchemaBreakingChange(
            f"breaking schema change for '{contract.name}': " + "; ".join(diff.breaking)
        )
    return diff
