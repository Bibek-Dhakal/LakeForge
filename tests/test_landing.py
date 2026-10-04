import pytest

from lakeforge.ingest.api import rows_from_payload
from lakeforge.ingest.landing import LandingIntegrityError, land
from lakeforge.settings import Settings


def test_landing_is_immutable_and_idempotent(tmp_path):
    settings = Settings.from_env().with_lake_root(tmp_path / "lake")
    calls = []

    def fetch(dest):
        calls.append(1)
        dest.write_text("hello")

    first = land(settings, "files", "2024-01", {"a.txt": fetch})
    second = land(settings, "files", "2024-01", {"a.txt": fetch})
    assert len(calls) == 1
    assert first.ingested_at == second.ingested_at

    first.path("a.txt").write_text("tampered")
    with pytest.raises(LandingIntegrityError):
        land(settings, "files", "2024-01", {"a.txt": fetch})


def test_weather_payload_rows():
    payload = {
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "temperature_2m_max": [5, 6.5],
            "temperature_2m_min": [1, None],
            "precipitation_sum": [0.0, 2.2],
        }
    }
    rows = rows_from_payload(payload)
    assert rows[0] == {
        "date": "2024-01-01",
        "temperature_2m_max": 5.0,
        "temperature_2m_min": 1.0,
        "precipitation_sum": 0.0,
    }
    assert rows[1]["temperature_2m_min"] is None


def test_weather_payload_without_days_is_rejected():
    with pytest.raises(ValueError):
        rows_from_payload({"daily": {}})
