"""Streamlit dashboard over the gold tables.

Run:  streamlit run src/lakeforge/serving/dashboard.py
Note: reads gold directly (trusted consumer). Use the API for role-scoped access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from deltalake import DeltaTable

LAKE_ROOT = Path(os.environ.get("LAKE_ROOT", "./data/lake")).resolve()


@st.cache_data(ttl=300)
def load(name: str) -> pd.DataFrame:
    path = (LAKE_ROOT / "gold" / name).as_posix()
    return DeltaTable(path).to_pyarrow_dataset().to_table().to_pandas()


st.set_page_config(page_title="LakeForge", layout="wide")
st.title("LakeForge: NYC taxi demand x weather")

try:
    daily = load("daily_summary").sort_values("pickup_date")
    fact = load("fact_trips_daily")
    zones = load("dim_zone")
except Exception as exc:  # table not built yet
    st.warning(f"Gold tables not available under {LAKE_ROOT}: {exc}")
    st.stop()

daily["revenue"] = daily["revenue"].astype(float)
col1, col2, col3 = st.columns(3)
col1.metric("Trips", f"{int(daily['trips'].sum()):,}")
col2.metric("Revenue ($)", f"{daily['revenue'].sum():,.0f}")
col3.metric("Days", f"{len(daily)}")

st.subheader("Trips per day")
st.line_chart(daily.set_index("pickup_date")["trips"])

st.subheader("Revenue vs precipitation")
st.scatter_chart(daily, x="precip_mm", y="revenue")

st.subheader("Top pickup zones")
top = (
    fact.groupby("pu_location_id", as_index=False)["trips"]
    .sum()
    .merge(zones, left_on="pu_location_id", right_on="zone_key", how="left")
    .sort_values("trips", ascending=False)
    .head(15)
)
st.bar_chart(top.set_index("zone")["trips"])
