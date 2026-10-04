"""Deterministic per-stage lineage records (inputs -> outputs), rewritten on every run."""

from __future__ import annotations

import json

from .settings import Settings


def record_lineage(
    settings: Settings, stage: str, batch_id: str, inputs: list[str], outputs: list[str]
) -> None:
    folder = settings.meta_dir / "lineage"
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "stage": stage,
        "batch_id": batch_id,
        "inputs": sorted(inputs),
        "outputs": sorted(outputs),
    }
    (folder / f"{stage}__{batch_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
