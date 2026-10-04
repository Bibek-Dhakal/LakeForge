"""Analytics API over lake tables: role-scoped SQL, row browsing, catalog, Prometheus metrics."""

from __future__ import annotations

from typing import Annotated, Any

import duckdb
from deltalake import DeltaTable
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..catalog import TABLES, table_path
from ..metrics import read_metrics, render_prometheus
from ..settings import Settings
from .access import Principal, authenticate, check_sql, load_policy, parse_api_keys


class SqlRequest(BaseModel):
    sql: str
    limit: int = 1000


def _connect(settings: Settings, tables: frozenset[str]) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB exposing ONLY the principal's tables; filesystem access then disabled."""
    con = duckdb.connect(":memory:")
    for name in sorted(tables):
        if name not in TABLES:
            continue
        path = table_path(settings, name)
        if DeltaTable.is_deltatable(path):
            con.register(name, DeltaTable(path).to_pyarrow_dataset())
    con.execute("SET enable_external_access=false")
    con.execute("SET lock_configuration=true")
    return con


def _run(con: duckdb.DuckDBPyConnection, sql: str, limit: int) -> dict[str, Any]:
    cur = con.execute(f"SELECT * FROM ({sql}) AS q LIMIT {int(limit)}")
    columns = [d[0] for d in cur.description]
    return {"columns": columns, "rows": jsonable_encoder(cur.fetchall())}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    keys = parse_api_keys(settings.api_keys)
    policy = load_policy(settings.policy_file)
    app = FastAPI(title="LakeForge Analytics API", version="0.1.0")

    def principal(x_api_key: Annotated[str | None, Header()] = None) -> Principal:
        who = authenticate(x_api_key, keys, policy)
        if who is None:
            raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")
        return who

    def clamp(limit: int) -> int:
        return max(1, min(limit, settings.max_query_rows))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics() -> str:
        return render_prometheus(read_metrics(settings), settings.freshness_slo_hours)

    @app.get("/tables")
    def list_tables(who: Principal = Depends(principal)) -> dict[str, Any]:
        items = []
        for name in sorted(who.tables):
            info = TABLES.get(name)
            if info is None:
                continue
            items.append(
                {
                    "name": name,
                    "layer": info.layer,
                    "description": info.description,
                    "materialised": DeltaTable.is_deltatable(table_path(settings, name)),
                }
            )
        return {"role": who.role, "tables": items}

    @app.get("/tables/{name}")
    def browse(
        name: str,
        limit: int = Query(100, ge=1),
        offset: int = Query(0, ge=0),
        who: Principal = Depends(principal),
    ) -> dict[str, Any]:
        if name not in who.tables:
            raise HTTPException(status_code=403, detail=f"role '{who.role}' cannot read {name}")
        if not DeltaTable.is_deltatable(table_path(settings, name)):
            raise HTTPException(status_code=404, detail=f"{name} is not materialised yet")
        con = _connect(settings, who.tables)
        try:
            return _run(con, f"SELECT * FROM {name} OFFSET {int(offset)}", clamp(limit))
        except duckdb.Error as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            con.close()

    @app.post("/query")
    def query(body: SqlRequest, who: Principal = Depends(principal)) -> dict[str, Any]:
        try:
            sql = check_sql(body.sql)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        con = _connect(settings, who.tables)
        try:
            return _run(con, sql, clamp(body.limit))
        except duckdb.Error as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            con.close()

    return app


app = create_app()
