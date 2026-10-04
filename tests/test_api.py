import pytest

pytest.importorskip("fastapi")
pytest.importorskip("duckdb")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from lakeforge.serving.app import create_app  # noqa: E402


@pytest.fixture()
def client(base_settings):
    return TestClient(create_app(base_settings))


def test_health_and_metrics_open(client):
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_tables_require_key(client):
    assert client.get("/tables").status_code == 401
    ok = client.get("/tables", headers={"X-API-Key": "k-analyst"})
    assert ok.status_code == 200 and ok.json()["role"] == "analyst"


def test_analyst_cannot_browse_quarantine(client):
    resp = client.get("/tables/quarantine_taxi_trips", headers={"X-API-Key": "k-analyst"})
    assert resp.status_code == 403


def test_query_guard_and_simple_select(client):
    headers = {"X-API-Key": "k-analyst"}
    assert client.post("/query", json={"sql": "DROP TABLE x"}, headers=headers).status_code == 400
    ok = client.post("/query", json={"sql": "SELECT 1 AS one"}, headers=headers)
    assert ok.status_code == 200 and ok.json()["rows"] == [[1]]
