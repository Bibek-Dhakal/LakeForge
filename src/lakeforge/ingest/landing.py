"""Immutable landing zone. A batch is written once (atomic rename) and verified on re-runs."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..metrics import iso, utcnow
from ..settings import Settings


class LandingIntegrityError(RuntimeError):
    """Raised when a landed file no longer matches its recorded checksum."""


@dataclass(frozen=True)
class LandingResult:
    source: str
    batch_id: str
    directory: Path
    manifest: dict[str, Any]

    @property
    def ingested_at(self) -> str:
        return self.manifest["ingested_at"]

    def path(self, name: str) -> Path:
        return self.directory / name


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(settings: Settings, source: str, batch_id: str) -> LandingResult:
    directory = settings.landing_dir(source, batch_id)
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"no landing manifest for {source}/{batch_id}; run ingest first")
    return LandingResult(source, batch_id, directory, json.loads(manifest_path.read_text()))


def land(
    settings: Settings,
    source: str,
    batch_id: str,
    fetchers: dict[str, Callable[[Path], None]],
) -> LandingResult:
    """Land a batch once. Re-runs verify checksums and reuse the original ingestion metadata."""
    target = settings.landing_dir(source, batch_id)
    if (target / "manifest.json").exists():
        result = read_manifest(settings, source, batch_id)
        for entry in result.manifest["files"]:
            path = target / entry["name"]
            if not path.exists() or sha256_of(path) != entry["sha256"]:
                raise LandingIntegrityError(f"landed file changed or missing: {path}")
        return result

    tmp = target.with_name(f"{batch_id}.tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    entries = []
    for name, fetch in fetchers.items():
        dest = tmp / name
        fetch(dest)
        entries.append({"name": name, "sha256": sha256_of(dest), "bytes": dest.stat().st_size})
    manifest = {
        "source": source,
        "batch_id": batch_id,
        "ingested_at": iso(utcnow()),
        "files": entries,
    }
    (tmp / "manifest.json").write_text(json.dumps(manifest, indent=2))
    if target.exists():
        shutil.rmtree(target)
    tmp.rename(target)
    return LandingResult(source, batch_id, target, manifest)
