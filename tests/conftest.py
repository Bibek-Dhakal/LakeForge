from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from lakeforge.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def base_settings(tmp_path_factory) -> Settings:
    return replace(
        Settings.from_env(),
        spark_master="local[2]",
        spark_shuffle_partitions=4,
        config_dir=ROOT / "config",
        lake_root=tmp_path_factory.mktemp("lake"),
        api_keys="k-analyst:analyst,k-ops:operator",
    )


@pytest.fixture(scope="session")
def spark(base_settings):
    pytest.importorskip("pyspark")
    pytest.importorskip("delta")
    from lakeforge.session import get_spark

    session = get_spark(base_settings, app="lakeforge-tests")
    yield session
    session.stop()
