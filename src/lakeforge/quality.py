"""Quality engine: declarative rules -> (valid rows, quarantined rows with rule + reason).

Invariant: input rows == valid rows + quarantined rows. Nothing is dropped or passed silently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pyspark.sql import Column, DataFrame, Window
from pyspark.sql import functions as F

RULE_TYPES = {"not_null", "range", "in_set", "regex", "expression", "unique", "referential"}
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class Rule:
    name: str
    type: str
    column: str | None = None
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)


def load_rules(path: Path | str, table: str) -> list[Rule]:
    spec = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if table not in spec:
        raise KeyError(f"no quality rules defined for table '{table}'")
    rules = []
    for raw in spec[table]:
        raw = dict(raw)
        rule = Rule(
            name=raw.pop("name"),
            type=raw.pop("type"),
            column=raw.pop("column", None),
            description=raw.pop("description", ""),
            params=raw,
        )
        if rule.type not in RULE_TYPES:
            raise ValueError(f"unknown rule type {rule.type!r} in rule {rule.name!r}")
        if not _NAME_RE.match(rule.name):
            raise ValueError(f"invalid rule name {rule.name!r}")
        rules.append(rule)
    return rules


def _row_flag(rule: Rule, context: dict[str, str]) -> Column:
    """Boolean column that is True when the row FAILS the rule."""
    p = rule.params
    c = F.col(rule.column) if rule.column else None
    if rule.type == "not_null":
        return c.isNull()
    if rule.type == "range":
        cond = F.lit(False)
        if "min" in p:
            cond = cond | (c < F.lit(p["min"]))
        if "max" in p:
            cond = cond | (c > F.lit(p["max"]))
        return F.coalesce(cond, F.lit(False))
    if rule.type == "in_set":
        return c.isNotNull() & ~c.isin(*p["values"])
    if rule.type == "regex":
        return c.isNotNull() & ~c.rlike(p["pattern"])
    if rule.type == "expression":
        return ~F.coalesce(F.expr(p["expr"].format(**context)), F.lit(False))
    raise ValueError(f"unsupported row rule {rule.type!r}")


def validate(
    df: DataFrame,
    rules: list[Rule],
    context: dict[str, str],
    refs: dict[str, DataFrame] | None = None,
) -> tuple[DataFrame, DataFrame]:
    """Return (valid, quarantine). `df` must carry _batch_id, _source and _ingested_at."""
    refs = refs or {}
    work = df
    flagged: list[tuple[Rule, str]] = []
    for rule in rules:
        flag = f"__f_{rule.name}"
        if rule.type == "referential":
            ref = (
                refs[rule.params["ref_table"]]
                .select(F.col(rule.params["ref_column"]).alias("__rk"))
                .distinct()
            )
            work = work.join(F.broadcast(ref), F.col(rule.column) == F.col("__rk"), "left")
            work = work.withColumn(flag, F.col(rule.column).isNotNull() & F.col("__rk").isNull())
            work = work.drop("__rk")
        elif rule.type == "unique":
            window = Window.partitionBy(rule.column).orderBy(*[F.col(c) for c in df.columns])
            work = work.withColumn(flag, F.row_number().over(window) > 1)
        else:
            work = work.withColumn(flag, _row_flag(rule, context))
        flagged.append((rule, flag))

    if flagged:
        names = [F.when(F.col(f), F.lit(r.name)) for r, f in flagged]
        reasons = [
            F.when(F.col(f), F.lit(r.name + (f": {r.description}" if r.description else "")))
            for r, f in flagged
        ]
        failed = F.filter(F.array(*names), lambda x: x.isNotNull())
        why = F.concat_ws("; ", *reasons)
    else:
        failed = F.array().cast("array<string>")
        why = F.lit("")

    work = work.withColumn("_failed_rules", failed).withColumn("_reasons", why).persist()
    valid = work.filter(F.size("_failed_rules") == 0).select(*df.columns)
    bad = work.filter(F.size("_failed_rules") > 0).select(
        "_batch_id",
        "_source",
        "_ingested_at",
        "_failed_rules",
        "_reasons",
        F.to_json(F.struct(*[F.col(c) for c in df.columns])).alias("_record"),
    )
    return valid, bad
