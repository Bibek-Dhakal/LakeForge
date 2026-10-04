"""Network helpers with bounded retries. Local paths are accepted for offline runs."""

from __future__ import annotations

import logging
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import requests

from ..settings import Settings

log = logging.getLogger(__name__)
T = TypeVar("T")


def _retry(fn: Callable[[], T], retries: int) -> T:
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except (requests.RequestException, OSError) as exc:
            if attempt == retries:
                raise
            wait = 2**attempt
            log.warning("attempt %d/%d failed (%s); retrying in %ds", attempt, retries, exc, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def download(src: str, dest: Path, settings: Settings) -> None:
    """Download an http(s) URL, or copy a local path / file:// URL, to `dest`."""
    if not src.startswith(("http://", "https://")):
        shutil.copyfile(src.removeprefix("file://"), dest)
        return

    def _go() -> None:
        with requests.get(src, stream=True, timeout=settings.http_timeout_s) as resp:
            resp.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)

    _retry(_go, settings.http_retries)


def get_text(url: str, settings: Settings, params: dict[str, Any] | None = None) -> str:
    def _go() -> str:
        resp = requests.get(url, params=params, timeout=settings.http_timeout_s)
        resp.raise_for_status()
        return resp.text

    return _retry(_go, settings.http_retries)
