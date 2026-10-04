from __future__ import annotations

from dataclasses import replace

import pytest

pytestmark = pytest.mark.spark


@pytest.fixture()
def env(tmp_path, base_settings):
    return replace(
        base_settings,
        lake_root=tmp_path / "lake",
        source_db_path=tmp_path / "ref.db",
        taxi_base_url=str(tmp_path / "src"),
        late_arrival_days=7,
    )
